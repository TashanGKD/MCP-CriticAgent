import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def main():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)

    # The query to get table schema is specific to PostgreSQL
    query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'mcp_test_results';
    """
    
    try:
        result = supabase.rpc('eval', {'query': query}).execute()
        print("Schema for mcp_test_results:")
        for row in result.data:
            print(f"  - {row['column_name']}: {row['data_type']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
