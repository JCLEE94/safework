#!/bin/bash

RUN_ID=15922996492
REPO="JCLEE94/safework"
CHECK_INTERVAL=10
TOTAL_CHECKS=6

echo "🚀 Starting pipeline monitoring for Run ID: $RUN_ID"
echo "Repository: $REPO"
echo "Monitoring interval: ${CHECK_INTERVAL}s"
echo "Total duration: $((TOTAL_CHECKS * CHECK_INTERVAL))s"
echo "=========================================="

for i in $(seq 1 $TOTAL_CHECKS); do
    echo -e "\n📊 Check $i/$TOTAL_CHECKS at $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Get run status
    RUN_STATUS=$(gh run view $RUN_ID --repo $REPO --json status,conclusion 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        STATUS=$(echo "$RUN_STATUS" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        CONCLUSION=$(echo "$RUN_STATUS" | grep -o '"conclusion":"[^"]*"' | cut -d'"' -f4)
        
        echo "Status: $STATUS"
        echo "Conclusion: $CONCLUSION"
        
        # Get job details
        echo -e "\n📋 Job Details:"
        gh run view $RUN_ID --repo $REPO | grep -E "JOBS|ID [0-9]+" | head -10
        
        # Check if completed
        if [ "$STATUS" = "completed" ]; then
            echo -e "\n✅ Pipeline completed!"
            if [ "$CONCLUSION" = "success" ]; then
                echo "🎉 SUCCESS - Pipeline passed!"
            else
                echo "❌ FAILURE - Pipeline failed with conclusion: $CONCLUSION"
                # Try to get failure details
                echo -e "\n📝 Attempting to fetch failure logs..."
                gh run view $RUN_ID --repo $REPO --log-failed 2>/dev/null | head -50
            fi
            break
        fi
    else
        echo "⚠️  Error fetching run status"
    fi
    
    if [ $i -lt $TOTAL_CHECKS ]; then
        echo -e "\n⏳ Waiting ${CHECK_INTERVAL}s for next check..."
        sleep $CHECK_INTERVAL
    fi
done

echo -e "\n=========================================="
echo "🏁 Monitoring complete at $(date '+%Y-%m-%d %H:%M:%S')"

# Final status check
FINAL_STATUS=$(gh run list --repo $REPO --limit 1 --json databaseId,status,conclusion | grep -E "(15922996492|status|conclusion)")
echo -e "\n📊 Final Pipeline Status:"
echo "$FINAL_STATUS"