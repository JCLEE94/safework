#!/bin/bash
# Health check script with retry logic

URL="${1:-https://safework.jclee.me/health}"
MAX_ATTEMPTS="${2:-10}"
WAIT_TIME="${3:-30}"

echo "🏥 Starting health check for: $URL"
echo "📊 Max attempts: $MAX_ATTEMPTS, Wait time: ${WAIT_TIME}s"

for i in $(seq 1 $MAX_ATTEMPTS); do
    echo -n "🔍 Attempt $i/$MAX_ATTEMPTS: "
    
    # Perform health check
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Success! (HTTP $HTTP_CODE)"
        
        # Get detailed health info
        HEALTH_INFO=$(curl -s "$URL")
        echo "📋 Health details: $HEALTH_INFO"
        
        exit 0
    else
        echo "❌ Failed (HTTP $HTTP_CODE)"
        
        if [ $i -lt $MAX_ATTEMPTS ]; then
            echo "⏳ Waiting ${WAIT_TIME}s before retry..."
            sleep $WAIT_TIME
        fi
    fi
done

echo "💔 Health check failed after $MAX_ATTEMPTS attempts"
exit 1