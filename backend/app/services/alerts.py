from sqlalchemy import text
from app.db.session import engine
from datetime import date

def check_and_trigger_alerts():
    """
    Checks the latest forecasts against user-defined price alerts.
    This is intended to be called after every successful model inference run.
    """
    print("Checking price alerts against latest forecasts...")
    try:
        with engine.connect() as conn:
            # 1. Get latest available forecasts for the next 3 days
            forecasts = conn.execute(text("""
                SELECT forecast_date, blended_prediction, fish, location
                FROM forecasts
                WHERE forecast_date >= CURRENT_DATE
                ORDER BY forecast_date ASC
            """)).fetchall()
            
            if not forecasts:
                print("No forecasts found to check against alerts.")
                return

            # 2. Get all active alerts
            alerts = conn.execute(text("""
                SELECT id, email, target_price, fish, location
                FROM price_alerts
                WHERE is_active = TRUE
            """)).fetchall()

            if not alerts:
                print("No active alerts found.")
                return

            triggered_count = 0
            for alert in alerts:
                # Find matching forecasts for the specific fish and location
                matches = [f for f in forecasts if f.fish == alert.fish and f.location == alert.location]
                
                for match in matches:
                    if float(match.blended_prediction) <= float(alert.target_price):
                        # MOCK: Notification logic
                        # In a real system, you would call an email service (SendGrid, Mailgun) or SMS gateway here.
                        print(f"!!! ALERT TRIGGERED !!!")
                        print(f"Recipient: {alert.email}")
                        print(f"Message: {alert.fish.capitalize()} price at {alert.location.capitalize()} is predicted to drop to Rs. {int(match.blended_prediction)} on {match.forecast_date}.")
                        print(f"User Target: Rs. {int(alert.target_price)}")
                        print("-" * 30)
                        triggered_count += 1
                        
                        # Optional: Deactivate alert after triggering once, or keep it active
                        # conn.execute(text("UPDATE price_alerts SET is_active = FALSE WHERE id = :id"), {"id": alert.id})
            
            print(f"Alert check completed. {triggered_count} alerts triggered.")

    except Exception as e:
        print(f"Error checking alerts: {e}")
