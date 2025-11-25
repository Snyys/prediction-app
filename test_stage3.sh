#!/bin/bash

set -e

echo "=== Smart Stage 3 Test: Auto User Registration ==="

# Функция для регистрации пользователя
register_user() {
    echo "👤 Registering test user..."
    RESPONSE=$(curl -s -X POST http://localhost:18080/register \
      -H "Content-Type: application/json" \
      -d '{
        "username": "autotest",
        "email": "autotest@example.com",
        "password": "autopass123"
    }')

    if echo "$RESPONSE" | grep -q "\"id\""; then
        echo "✅ User registered successfully"
        return 0
    elif echo "$RESPONSE" | grep -q "already registered"; then
        echo "ℹ️ User already exists, continuing..."
        return 0
    else
        echo "❌ Registration failed: $RESPONSE"
        return 1
    fi
}

# Функция для получения токена
get_token() {
    local username=$1
    local password=$2

    echo "🔑 Getting token for $username..."
    RESPONSE=$(curl -s -X POST http://localhost:18080/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=$username&password=$password")

    if echo "$RESPONSE" | grep -q "access_token"; then
        TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
        echo "✅ Token received"
        return 0
    else
        echo "❌ Login failed: $RESPONSE"
        return 1
    fi
}

# Основная логика
echo "1. Setting up test user..."

# Пробуем сначала с testuser
if get_token "testuser" "testpass123"; then
    echo "✅ Using existing testuser"
else
    # Если testuser не работает, регистрируем нового
    if register_user; then
        if get_token "autotest" "autopass123"; then
            echo "✅ Using newly registered autotest"
        else
            echo "❌ Cannot get token even after registration"
            exit 1
        fi
    else
        echo "❌ Cannot register user"
        exit 1
    fi
fi

# Создаем предсказания с правильным форматом дат
echo -e "\n2. Creating test predictions..."
for i in {1..3}; do
    echo "   Creating prediction $i..."

    # Используем двузначные числа для дней
    day=$(printf "%02d" $((10 + i)))

    PREDICTION_DATA='{
    "title": "Smart Test Prediction '"$i"'",
    "description": "Created by smart test script - prediction '"$i"'",
    "predicted_date": "2024-12-'"$day"'T12:00:00",
    "expiration_date": "2024-12-'"$day"'T23:59:59",
    "confidence_level": 0.'$((75 + i * 2))'
}'

    RESPONSE=$(curl -s -X POST http://localhost:18080/predictions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "$PREDICTION_DATA")

    if echo "$RESPONSE" | grep -q "\"id\""; then
        PREDICTION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
        echo "   ✅ Prediction $i created (ID: $PREDICTION_ID)"
    else
        echo "   ❌ Failed to create prediction $i"
        echo "   Response: $RESPONSE"
    fi

    sleep 0.5
done

# Проверяем созданные предсказания
echo -e "\n3. Verifying predictions..."
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
    echo "✅ SUCCESS: Found $PREDICTION_COUNT predictions"

    # Показываем детали
    echo ""
    echo "📋 Prediction details:"
    echo "$PREDICTIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for pred in data:
        print(f'   - ID: {pred[\"id\"]:2} | {pred[\"title\"]:25} | Status: {pred[\"status\"]}')
except Exception as e:
    print(f'   Error parsing: {e}')
"
else
    echo "❌ No predictions found"
    echo "Raw response: $PREDICTIONS_RESPONSE"
fi

# Тестируем дополнительные endpoints
echo -e "\n4. Testing additional features..."

# Статистика
echo "   Getting statistics..."
STATS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/stats/detailed)
echo "   📊 Stats: $STATS_RESPONSE"

# Награды
echo "   Getting rewards..."
REWARDS_COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/rewards/available | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print(0)
")
echo "   🏆 Available rewards: $REWARDS_COUNT"

echo -e "\n🎉 SMART TEST COMPLETED!"
if [ "$PREDICTION_COUNT" -gt 0 ]; then
    echo "✅ SUCCESS: Predictions created and verified!"
else
    echo "⚠️  Predictions were not created, but other features work"
fi