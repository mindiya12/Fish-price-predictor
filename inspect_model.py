
import joblib
import os

model_path = 'd:/fish-price-forecast/backend/models/balaya_h1.pkl'
model = joblib.load(model_path)
print("Type:", type(model))
print("Model:", model)

# If it has feature_names_in_ (sklearn/xgboost)
if hasattr(model, 'feature_names_in_'):
    print("\nFeature names:", list(model.feature_names_in_))
elif hasattr(model, 'get_booster'):
    booster = model.get_booster()
    print("\nFeature names:", booster.feature_names)
elif hasattr(model, 'named_steps'):
    print("\nPipeline steps:", list(model.named_steps.keys()))
    last_step = list(model.named_steps.values())[-1]
    if hasattr(last_step, 'feature_names_in_'):
        print("Feature names:", list(last_step.feature_names_in_))
    elif hasattr(last_step, 'get_booster'):
        print("Feature names:", last_step.get_booster().feature_names)
