import os
import json
from report_manager import ReportManager
from dotenv import load_dotenv

# Charger les variables d'env (pour AzureWebJobsStorage)
load_dotenv()

def check_recent():
    manager = ReportManager()
    reports = manager.get_latest_reports(limit=10)
    
    print(f"Trouvé {len(reports)} rapports récents.\n")
    for r in reports:
        ts = r.get('timestamp')
        type_ = r.get('type')
        status = r.get('status')
        updated = r.get('total_updated', 0)
        print(f"[{ts}] Type: {type_} | Status: {status} | Updated: {updated}")
        if updated > 0:
            print(f"   Logs: {r.get('raw_logs', '')[:200]}...")

if __name__ == "__main__":
    check_recent()
