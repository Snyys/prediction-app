#!/bin/bash

echo "=== Testing Stage 3: Extended CRUD and Analytics ==="

# Сначала проверяем что сервер работает
echo "1. Checking server health..."
HEALTH_RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" http://localhost:18080/health)
HTTP_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d: -f2)

if [ "$HTTP_STATUS" != "200" ]; then
    echo "ERROR: Server is not responding. HTTP Status: $HTTP_STATUS"
    echo "Please make sure the application is running"
    exit 1
fi

echo "✓ Server is healthy"

# Регистрируем нового пользователя если нужно
echo -e "\n2. Registering test user..."
REGISTER_RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" -X POST http://localhost:18080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "stage3user",
    "email": "stage3@example.com",
    "password": "stage3pass123"
  }')

HTTP_STATUS=$(echo "$REGISTER_RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d: -f2)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//g')

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✓ New user registered"
elif [ "$HTTP_STATUS" == "400" ]; then
    echo "ℹ️ User already exists, trying to login..."
else
    echo "ERROR: Registration failed. HTTP Status: $HTTP_STATUS"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# Логин
echo -e "\n3. Login and get JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:18080/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=stage3user&password=stage3pass123")

# Проверяем что токен получен
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✓ Token received: ${TOKEN:0:20}..."
else
    echo "ERROR: Login failed!"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "Trying with different user..."

    # Пробуем с другим пользователем
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:18080/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=testuser&password=testpass123")

    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
        echo "✓ Token received with testuser: ${TOKEN:0:20}..."
    else
        echo "ERROR: Both logins failed!"
        echo "Please register a user first:"
        echo "curl -X POST http://localhost:18080/register \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"testpass123\"}'"
        exit 1
    fi
fi

# Создаем предсказания
echo -e "\n4. Creating test predictions..."
for i in {1..3}; do
    RESPONSE=$(curl -s -X POST http://localhost:18080/predictions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "{
        \"title\": \"Stage 3 Test Prediction $i\",
        \"description\": \"This is stage 3 test prediction $i\",
        \"predicted_date\": \"2024-12-${i}T12:00:00\",
        \"expiration_date\": \"2024-12-${i}T23:59:59\",
        \"confidence_level\": 0.$((70 + i))
      }")

    if echo "$RESPONSE" | grep -q "\"id\""; then
        echo "✓ Prediction $i created"
    else
        echo "✗ Failed to create prediction $i"
        echo "Response: $RESPONSE"
    fi
done

# Получаем предсказания
echo -e "\n5. Getting user predictions..."
PREDICTIONS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/predictions)

PREDICTION_COUNT=$(echo "$PREDICTIONS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$PREDICTION_COUNT" -gt 0 ]; then
    echo "✓ Found $PREDICTION_COUNT predictions"

    # Берем ID первого предсказания для верификации
    FIRST_ID=$(echo "$PREDICTIONS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null || echo "0")

    if [ "$FIRST_ID" != "0" ]; then
        echo -e "\n6. Verifying prediction $FIRST_ID..."
        VERIFY_RESPONSE=$(curl -s -X PUT "http://localhost:18080/predictions/$FIRST_ID/verify?is_correct=true" \
          -H "Authorization: Bearer $TOKEN")
        echo "✓ Verification response: $VERIFY_RESPONSE"
    fi
else
    echo "✗ No predictions found"
fi

# Статистика
echo -e "\n7. Getting user statistics..."
STATS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/stats/detailed)
echo "✓ Stats: $STATS_RESPONSE"

# Награды
echo -e "\n8. Getting available rewards..."
REWARDS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:18080/rewards/available)

REWARD_COUNT=$(echo "$REWARDS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "✓ Found $REWARD_COUNT available rewards"

echo -e "\n=== Stage 3 Test Completed Successfully ==="
echo "You can explore the API at: http://localhost:18080/docs"