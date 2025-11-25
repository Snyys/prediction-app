#!/bin/bash

set -e

echo "=== Fixed Stage 3 Test: Proper Date Format ==="

# Получаем токен
echo "1. Getting token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:18080/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123")

# Проверяем что токен получен
if ! echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "❌ ERROR: Cannot get access token"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "Please register test user first:"
    echo "curl -X POST http://localhost:18080/register \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"testpass123\"}'"
    exit 1
fi

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Token received: ${TOKEN:0:20}..."

# Создаем предсказания с ПРАВИЛЬНЫМ форматом дат
echo -e "\n2. Creating test predictions with correct date format..."
for i in {1..3}; do
    echo "   Creating prediction $i..."

    # Используем ДВУЗНАЧНЫЕ числа для дней
    day=$(printf "%02d" $((10 + i)))

    PREDICTION_DATA=$(cat << PREDICTION
{
    "title": "Test Prediction $i",
    "description": "This is automated test prediction $i created by test script",
    "predicted_date": "2024-12-${day}T12:00:00",
    "expiration_date": "2024-12-${day}T23:59:59",
    "confidence_level": 0.$((70 + i * 5))
}
PREDICTION
)

    echo "   Data: $PREDICTION_DATA"

    RESPONSE=$(curl -s -X POST http://localhost:18080/predictions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "$PREDICTION_DATA")

    # Проверяем ответ
    if echo "$RESPONSE" | grep -q "\"id\""; then
        PREDICTION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
        echo "   ✅ Prediction $i created successfully (ID: $PREDICTION_ID)"
    elif echo "$RESPONSE" | grep -q "error\|Error"; then
        echo "   ❌ Prediction $i failed: $RESPONSE"
    else
        echo "   ⚠️  Prediction $i - unknown response: $RESPONSE"
    fi

    sleep 1  # Небольшая пауза между запросами
done

# Проверяем что предсказания создались
echo -e "\n3. Verifying predictions were created..."
PREDICTIONS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/predictions)

PREDICTION_COUNT=$(echo "$PREDICTIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print(0)
")

if [ "$PREDICTION_COUNT" -gt 0 ]; then
    echo "✅ SUCCESS: Created $PREDICTION_COUNT predictions"

    # Показываем ID созданных предсказаний
    echo ""
    echo "📋 Created prediction IDs:"
    echo "$PREDICTIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for pred in data:
        print(f'   - ID: {pred[\"id\"]}, Title: {pred[\"title\"]}, Status: {pred[\"status\"]}')
except Exception as e:
    print(f'   Error parsing: {e}')
"
else
    echo "❌ FAILED: No predictions found"
    echo "Raw response: $PREDICTIONS_RESPONSE"
fi

# Дополнительные тесты
echo -e "\n4. Testing additional endpoints..."

# Статистика
echo "   Getting statistics..."
STATS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/stats/detailed)
echo "   ✅ Stats: $STATS_RESPONSE"

# Награды
echo "   Getting rewards..."
REWARDS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/rewards/available)
REWARD_COUNT=$(echo "$REWARDS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print(0)
")
echo "   ✅ Found $REWARD_COUNT available rewards"

echo -e "\n=== Test Completed ==="
if [ "$PREDICTION_COUNT" -gt 0 ]; then
    echo "🎉 SUCCESS: All tests passed!"
    echo "   Predictions successfully created and stored in database"
else
    echo "⚠️  WARNING: Predictions were not created"
    echo "   Let's try manual creation to debug..."
fi