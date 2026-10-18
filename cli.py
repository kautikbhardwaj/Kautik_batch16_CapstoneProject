#!/usr/bin/env python3
"""
DevOps Multi-Cloud Cost & Resource Monitor - Administrative CLI Tool
Designed for automated cron jobs, CI/CD pipelines, and DevOps administrators.
"""

import sys
import os
import argparse
import csv
import json

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import engine, Base, SessionLocal
from backend.app.models import CostRecord, ResourceMetric, AlertIncident, ProviderStatus
from backend.app.services.aggregator import CloudDataAggregator
from backend.app.services.optimizer import CostOptimizationEngine
from backend.app.services.anomaly import AnomalyDetectionEngine
from backend.app.services.notifier import NotificationDispatcher
import asyncio


def cmd_sync(args):
    print(f"[*] Starting multi-cloud synchronization (lookback: {args.days} days)...")
    db = SessionLocal()
    try:
        res = CloudDataAggregator.sync_all_clouds(db, days_back=args.days)
        print("[+] Synchronization complete!")
        print(f"    - Cost Records Ingested:    {res['summary']['total_cost_records']}")
        print(f"    - Metric Records Ingested:  {res['summary']['total_metrics_records']}")
        for provider, stats in res['providers'].items():
            print(f"    - {provider}: {stats['status'].upper()} ({stats['costs_synced']} cost rows)")
    finally:
        db.close()


def cmd_status(args):
    db = SessionLocal()
    try:
        print("\n" + "=" * 65)
        print("  CLOUD PROVIDER CONNECTIVITY & INGESTION STATUS")
        print("=" * 65)
        statuses = db.query(ProviderStatus).all()
        for s in statuses:
            print(f"  [{s.provider:5}] Status: {s.status.upper():10} | Records: {s.records_synced:5} | Last Sync: {s.last_sync_at}")
        
        alerts_count = db.query(AlertIncident).filter(AlertIncident.status == "active").count()
        savings = CostOptimizationEngine.get_total_potential_savings(db)
        print("-" * 65)
        print(f"  Active Critical/Warning Incidents: {alerts_count}")
        print(f"  Identified FinOps Monthly Savings: ${savings:,.2f}")
        print("=" * 65 + "\n")
    finally:
        db.close()


def cmd_optimize(args):
    db = SessionLocal()
    try:
        print("\n[*] Evaluating FinOps Cost Optimization Opportunities...")
        recs = CostOptimizationEngine.evaluate_optimizations(db)
        total_savings = CostOptimizationEngine.get_total_potential_savings(db)
        print(f"[+] Found {len(recs)} actionable recommendations. Total Monthly Savings: ${total_savings:,.2f}\n")
        print(f"{'TYPE':<20} | {'PROVIDER':<8} | {'EST SAVINGS':<12} | {'TITLE'}")
        print("-" * 75)
        for r in recs:
            print(f"{r.recommendation_type:<20} | {r.provider:<8} | ${r.estimated_monthly_savings:>9.2f} | {r.title}")
    finally:
        db.close()


def cmd_anomalies(args):
    db = SessionLocal()
    try:
        print(f"\n[*] Scanning for cost anomalies (Z-Score Threshold: > {args.threshold})...")
        anomalies = AnomalyDetectionEngine.calculate_cost_anomalies(db, z_threshold=args.threshold, days_lookback=args.days)
        if not anomalies:
            print("[+] No anomalous spend spikes detected within criteria.")
            return

        print(f"[!] Detected {len(anomalies)} cost anomalies:\n")
        print(f"{'DATE':<11} | {'PROVIDER':<8} | {'SERVICE':<15} | {'ACTUAL':<10} | {'BASELINE':<10} | {'Z-SCORE':<8} | {'SPIKE %'}")
        print("-" * 80)
        for a in anomalies:
            print(f"{a['date']:<11} | {a['provider']:<8} | {a['service']:<15} | ${a['actual_cost']:<9.2f} | ${a['expected_baseline']:<9.2f} | {a['z_score']:<8.2f} | +{a['percent_spike']:.1f}%")
    finally:
        db.close()


def cmd_export_csv(args):
    db = SessionLocal()
    try:
        out_path = args.output
        records = db.query(CostRecord).order_by(CostRecord.record_date.desc()).all()
        print(f"[*] Exporting {len(records)} cost records to {out_path}...")
        
        with open(out_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["record_date", "provider", "service", "resource_id", "environment", "region", "cost_usd", "usage_amount", "usage_unit"])
            for r in records:
                writer.writerow([r.record_date, r.provider, r.service, r.resource_id, r.environment, r.region, r.cost_usd, r.usage_amount, r.usage_unit])
        
        print(f"[+] Successfully exported {len(records)} rows to {out_path}")
    finally:
        db.close()


def cmd_test_alert(args):
    print(f"[*] Sending test alert payload via {args.channel.upper()} dispatcher...")
    success = False
    if args.channel.lower() == "teams":
        success = asyncio.run(NotificationDispatcher.send_teams_alert(
            webhook_url=None,
            title="[CLI Test] Microsoft Teams Alert",
            message="Test dispatch from DevOps Dashboard CLI utility.",
            severity="warning"
        ))
    else:
        success = asyncio.run(NotificationDispatcher.send_slack_alert(
            webhook_url=None,
            title="[CLI Test] Multi-Cloud Spend Anomaly",
            message="Test dispatch from DevOps Dashboard CLI utility.",
            severity="critical",
            metadata={"Source": "DevOps CLI", "TriggeredBy": "Administrator"}
        ))
    print(f"[+] Alert dispatch result: {'SUCCESS' if success else 'FAILED'}")


def main():
    Base.metadata.create_all(bind=engine)

    parser = argparse.ArgumentParser(description="DevOps Multi-Cloud Dashboard Administrator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # sync
    p_sync = subparsers.add_parser("sync", help="Trigger cloud cost and metric ingestion")
    p_sync.add_argument("--days", type=int, default=30, help="Days of historical data to pull")
    p_sync.set_defaults(func=cmd_sync)

    # status
    p_status = subparsers.add_parser("status", help="Display provider connectivity and health status")
    p_status.set_defaults(func=cmd_status)

    # optimize
    p_opt = subparsers.add_parser("optimize", help="Run FinOps cost optimization and waste analysis")
    p_opt.set_defaults(func=cmd_optimize)

    # anomalies
    p_anom = subparsers.add_parser("anomalies", help="Run statistical Z-Score anomaly detection")
    p_anom.add_argument("--threshold", type=float, default=2.0, help="Z-score threshold")
    p_anom.add_argument("--days", type=int, default=30, help="Days to analyze")
    p_anom.set_defaults(func=cmd_anomalies)

    # export-csv
    p_csv = subparsers.add_parser("export-csv", help="Export cost ledger to CSV file")
    p_csv.add_argument("--output", type=str, default="cloud_spend_ledger.csv", help="Output file path")
    p_csv.set_defaults(func=cmd_export_csv)

    # test-alert
    p_alert = subparsers.add_parser("test-alert", help="Send test webhook notification")
    p_alert.add_argument("--channel", type=str, default="slack", choices=["slack", "teams"], help="Notification target channel")
    p_alert.set_defaults(func=cmd_test_alert)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
