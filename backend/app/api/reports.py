from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy import text
from app.db.session import engine
import io
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'FishPrice.LK - Procurement Intelligence Report', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

@router.get("/procurement")
def generate_procurement_report(fish: str = "balaya", location: str = "peliyagoda"):
    # Fetch forecast data
    query = text("""
        SELECT forecast_date, horizon, blended_prediction
        FROM forecasts
        WHERE fish = :fish AND location = :location
        ORDER BY forecast_date ASC, horizon ASC
        LIMIT 3
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"fish": fish, "location": location}).fetchall()
    
    if not rows:
        return {"error": "No forecast data available for report generation"}

    pdf = PDF()
    pdf.add_page()
    
    # Summary Section
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, f'Market Insight: {fish.capitalize()} at {location.capitalize()}', 0, 1)
    pdf.ln(5)
    
    # Best Day logic
    best_row = min(rows, key=lambda x: x.blended_prediction)
    avg_price = sum(r.blended_prediction for r in rows) / len(rows)
    
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, f"Analysis of the upcoming 3-day window reveals that {best_row.forecast_date} is the most cost-effective day for procurement, with a predicted price of Rs. {int(best_row.blended_prediction)} per kg.")
    pdf.ln(5)

    # Data Table
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(60, 10, 'Date', 1, 0, 'C', 1)
    pdf.cell(60, 10, 'Predicted Price (Rs.)', 1, 0, 'C', 1)
    pdf.cell(60, 10, 'Market Outlook', 1, 1, 'C', 1)
    
    pdf.set_font('Helvetica', '', 11)
    for r in rows:
        outlook = "Stable"
        if r.blended_prediction < avg_price * 0.95: outlook = "Bargain"
        if r.blended_prediction > avg_price * 1.05: outlook = "High Demand"
        
        pdf.cell(60, 10, str(r.forecast_date), 1, 0, 'C')
        pdf.cell(60, 10, f"Rs. {int(r.blended_prediction)}", 1, 0, 'C')
        pdf.cell(60, 10, outlook, 1, 1, 'C')

    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'Procurement Recommendation', 0, 1)
    pdf.set_font('Helvetica', '', 11)
    
    rec_text = (
        f"Based on our XGBoost forecasting models, we recommend bulk procurement on {best_row.forecast_date}. "
        f"The predicted price is approximately {round(((avg_price - best_row.blended_prediction)/avg_price)*100, 1)}% "
        f"lower than the window average (Rs. {int(avg_price)})."
    )
    pdf.multi_cell(0, 8, rec_text)

    # Output as stream
    pdf_out = pdf.output(dest='S')
    return Response(
        content=pdf_out,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=procurement_report_{fish}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )
