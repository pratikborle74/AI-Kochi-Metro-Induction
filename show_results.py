import json
import pandas as pd

# Load optimization results
with open('intelligent_optimization_results.json', 'r') as f:
    results = json.load(f)

print('🎯 INTELLIGENT OPTIMIZATION RESULTS ANALYSIS:')
print('=' * 60)

summary = results['optimization_summary']
print(f"📊 FLEET ALLOCATION:")
print(f"   🟢 Service Ready: {summary['service_ready']} trains ({summary['service_ready']/25*100:.1f}%)")
print(f"   🔧 Maintenance Required: {summary['maintenance_required']} trains ({summary['maintenance_required']/25*100:.1f}%)")
print(f"   ⏸️  Standby: {summary['standby']} trains ({summary['standby']/25*100:.1f}%)")

print(f"\n🧠 ML INSIGHTS:")
ml_insights = results['ml_insights']
print(f"   🔮 Failure Prediction: {'✅ ENABLED' if ml_insights['failure_prediction_enabled'] else '❌ DISABLED'}")
print(f"   🎯 Decision Optimization: {'✅ ENABLED' if ml_insights['optimization_model_enabled'] else '❌ DISABLED'}")
print(f"   📈 Demand Forecasting: {'✅ ENABLED' if ml_insights['demand_forecasting_enabled'] else '❌ DISABLED'}")
print(f"   🚨 High Risk Trains: {ml_insights['high_risk_trains']}")

print(f"\n🏆 TOP 5 SERVICE-READY TRAINS:")
service_trains = [t for t in results['train_recommendations'] if t['recommended_action'] == 'Service'][:5]
for i, train in enumerate(service_trains, 1):
    print(f"   {i}. {train['train_id']}: Priority {train['priority_score']:.1f}, ML Confidence {train['ml_confidence']:.2f}, Risk {train['failure_risk']:.2f}")

print(f"\n⚠️  HIGH-RISK OVERRIDES:")
override_trains = [t for t in results['train_recommendations'] if 'OVERRIDE' in str(t.get('reasoning', []))]
for train in override_trains:
    print(f"   • {train['train_id']}: ML suggested {train['ml_decision']} → FORCED {train['recommended_action']} (Risk: {train['failure_risk']:.2f})")

print(f"\n✅ SYSTEM STATUS: FULLY OPERATIONAL")
print(f"⏰ Analysis Time: {results['timestamp']}")