
import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError
import pandas as pd

from prompts import LOAN_ANALYSIS_PROMPT_TEMPLATE

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_TABLES = {
    "commercial_real_estate": "ccibt-hack25ww7-719.Genavate_real_estae_data.commercial_real_estate",
    "realtor_data": "ccibt-hack25ww7-719.Genavate_real_estae_data.realtor_data",
    "nfip_losses_by_state": "ccibt-hack25ww7-719.Genavate_real_estae_data.nfip_financial-losses-by-state__20251031",
    "nfip_losses_by_zone": "ccibt-hack25ww7-719.Genavate_real_estae_data.nfip_policy-and-loss-statistics-by-flood-zone",
    "safmrs_revised": "ccibt-hack25ww7-719.Genavate_real_estae_data.safmrs_revised",
    "fy2026_safmrs": "ccibt-hack25ww7-719.Genavate_real_estae_data.fy2026_safmrs",
}

def _extract_property_details(file_content: str) -> dict:
    """Extracts location and property details from text content."""
    details = {"state": None, "city": None, "zip": None, "property_type": None, "sqft": None}
    
    # Simple extraction logic using regex
    details['zip'] = (re.search(r'\b\d{5}\b', file_content) or {}).get(0)
    state_match = re.search(r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b', file_content, re.IGNORECASE)
    if state_match:
        details['state'] = state_match.group(0).upper()
        city_match = re.search(r'([A-Za-z\s]+)(?:,\s*|\s+)' + re.escape(details['state']), file_content, re.IGNORECASE)
        if city_match:
            details['city'] = city_match.group(1).strip().title()

    prop_type_match = re.search(r'(office|retail|industrial|multifamily|land)', file_content, re.IGNORECASE)
    if prop_type_match:
        details['property_type'] = prop_type_match.group(0).lower()

    sqft_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)\s*(?:sqft|sf|sq\.? ft\.?)', file_content, re.IGNORECASE)
    if sqft_match:
        details['sqft'] = int(sqft_match.group(1).replace(',', ''))
        
    return details

def _fetch_bigquery_context(details: dict) -> str:
    """Fetches relevant data from BigQuery based on extracted property details."""
    if not details.get("state"):
        return "No location information could be extracted to query BigQuery."

    context_parts = []
    try:
        client = bigquery.Client(project=GCP_PROJECT_ID)
        state = details["state"]
        city = details.get("city")
        prop_type = details.get("property_type")
        sqft = details.get("sqft")

        params = [bigquery.ScalarQueryParameter("state", "STRING", state)]
        
        # --- More Intelligent Queries ---
        
        # Query 1: Realtor Data - Find comps with similar size and type
        realtor_query = f"SELECT city, state, price, beds, baths, sqft FROM `{BIGQUERY_TABLES['realtor_data']}` WHERE state = @state"
        if city:
            realtor_query += " AND city = @city"
            params.append(bigquery.ScalarQueryParameter("city", "STRING", city))
        if sqft:
            realtor_query += " AND sqft BETWEEN @sqft_min AND @sqft_max"
            params.append(bigquery.ScalarQueryParameter("sqft_min", "INT64", int(sqft * 0.8)))
            params.append(bigquery.ScalarQueryParameter("sqft_max", "INT64", int(sqft * 1.2)))
        realtor_query += " LIMIT 5"
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = client.query(realtor_query, job_config=job_config).to_dataframe()
        if not results.empty:
            context_parts.append(f"Realtor Market Data:\n{results.to_json(orient='records')}")

        # Query 2: Commercial Real Estate Data - Find comps with similar type
        comm_query = f"SELECT sale_price, city, state, property_type, year_built FROM `{BIGQUERY_TABLES['commercial_real_estate']}` WHERE state = @state"
        comm_params = [bigquery.ScalarQueryParameter("state", "STRING", state)]
        if prop_type:
            comm_query += " AND LOWER(property_type) = @prop_type"
            comm_params.append(bigquery.ScalarQueryParameter("prop_type", "STRING", prop_type))
        comm_query += " LIMIT 5"
        
        job_config = bigquery.QueryJobConfig(query_parameters=comm_params)
        results = client.query(comm_query, job_config=job_config).to_dataframe()
        if not results.empty:
            context_parts.append(f"Commercial Real Estate Comps:\n{results.to_json(orient='records')}")

        # Query 3: NFIP Financial Losses by State
        nfip_query = f"SELECT state, amount_paid_on_claims FROM `{BIGQUERY_TABLES['nfip_losses_by_state']}` WHERE state = @state LIMIT 1"
        job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("state", "STRING", state)])
        results = client.query(nfip_query, job_config=job_config).to_dataframe()
        if not results.empty:
            context_parts.append(f"NFIP Financial Losses Data:\n{results.to_json(orient='records')}")

        # Query 4: SAFMRS Revised Risk Data
        safmrs_query = f"SELECT state, risk_summary, last_updated FROM `{BIGQUERY_TABLES['safmrs_revised']}` WHERE state = @state ORDER BY last_updated DESC LIMIT 1"
        job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("state", "STRING", state)])
        try:
            results = client.query(safmrs_query, job_config=job_config).to_dataframe()
            if not results.empty:
                context_parts.append(f"Internal SAFMRS Risk Data:\n{results.to_json(orient='records')}")
        except GoogleAPICallError as e:
            print(f"Could not query SAFMRS table, may not exist or schema differs: {e.message}")

        if not context_parts:
            return "No relevant data found in BigQuery for the specified location."

        return "\n\n".join(context_parts)

    except GoogleAPICallError as e:
        print(f"BigQuery API Error: {e}")
        return f"Error accessing BigQuery. Please check GCP project permissions and table names. Details: {e.message}"
    except Exception as e:
        print(f"An unexpected error occurred during BigQuery fetch: {e}")
        return "An unexpected error occurred while fetching data from BigQuery."


async def get_analysis_memo(file_content: str) -> str:
    """
    Uses LangChain and Google Gemini to analyze the provided text content,
    enriched with data from Google BigQuery.
    """
    details = _extract_property_details(file_content)
    bigquery_context = _fetch_bigquery_context(details)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("API_KEY"))

    prompt = PromptTemplate(
        template=LOAN_ANALYSIS_PROMPT_TEMPLATE,
        input_variables=["file_content", "bigquery_context"],
    )

    chain = prompt | llm | StrOutputParser()
    response = await chain.ainvoke({
        "file_content": file_content,
        "bigquery_context": bigquery_context
    })

    return response
