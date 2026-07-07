#!/bin/bash
# 平日毎朝 7:30 に実行
# crontab: 30 7 * * 1-5 /opt/production/cron_generate.sh >> /opt/production/logs/cron.log 2>&1

cd /opt/production   # ← NASのパスに合わせて変更
export SLACK_BOT_TOKEN="xoxb-xxxx-xxxx-xxxx"
export SLACK_CHANNEL="C06DBE9536Y"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 生産計画生成開始 ==="
python3 generate_plan.py --slack
echo "=== $(date '+%Y-%m-%d %H:%M:%S') 完了 ==="
