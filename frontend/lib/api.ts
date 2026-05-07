export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 1. Fetch the latest 7-day forecast
export async function getLatestForecast(fish = "balaya", location = "peliyagoda") {
    const response = await fetch(`${API_BASE_URL}/api/forecast/latest?fish=${fish}&location=${location}`);
    if (!response.ok) {
        throw new Error("Failed to fetch forecast");
    }
    return response.json();
}

// 2. Fetch historical prices for a date range
export async function getHistory(fromDate: string, toDate: string, fish = "balaya", location = "peliyagoda") {
    const response = await fetch(`${API_BASE_URL}/api/history?from=${fromDate}&to=${toDate}&fish=${fish}&location=${location}`);
    if (!response.ok) {
        throw new Error("Failed to fetch history");
    }
    return response.json();
}

// 3. Get the raw URL for the download buttons
export function getDownloadUrl(fromDate: string, toDate: string, format: "csv" | "excel" = "csv") {
    return `${API_BASE_URL}/api/download/history?from=${fromDate}&to=${toDate}&format=${format}&fish=balaya&location=peliyagoda`;
}

// 4. Get today's price (actual or forecast)
export async function getTodayPrice(fish = "balaya", location = "peliyagoda") {
    const response = await fetch(`${API_BASE_URL}/api/today-price?fish=${fish}&location=${location}`);
    if (!response.ok) {
        throw new Error("Failed to fetch today's price");
    }
    return response.json();
}
