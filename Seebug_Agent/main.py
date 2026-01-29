import os
import sys
from seebug_client import SeebugAPIClient
from poc_generator import POCGenerator

# User provided API Key
SEEBUG_API_KEY = "a1c22e6365df93275fa82397dbbdbbb7d9c6a75b"

def main():
    print("🚀 Starting Seebug POC Intelligent Agent...")
    
    # 1. Initialize Seebug Client
    client = SeebugAPIClient(api_key=SEEBUG_API_KEY)
    # if not client.is_valid:
    #     print("❌ Seebug API Key invalid. Exiting.")
    #     return

    # 2. Search for Vulnerabilities
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        print(f"🔍 Using keyword from arguments: {keyword}")
    else:
        keyword = input("🔍 Enter keyword to search for vulnerabilities (e.g., thinkphp, redis): ").strip()
        
    if not keyword:
        print("Keyword cannot be empty.")
        return

    print(f"Searching for '{keyword}'...")
    search_result = client.search_poc(keyword=keyword, page=1, page_size=5)
    
    if search_result.get("status") != "success":
        print(f"❌ Search failed: {search_result.get('msg', 'Unknown error')}")
        return

    poc_list = search_result["data"]["list"]
    if not poc_list:
        print(f"⚠️ Search successful but no results found for '{keyword}'.")
        print("ℹ️ Note: Seebug API may only return POCs available to your account tier.")
        
        print("\n⚠️ Switching to manual input mode for testing AI generation...")
        
        # Fallback for testing/manual input
        vul_info = {
            "name": keyword,
            "type": "Web Vulnerability",
            "description": f"This is a test description for {keyword}. The target is vulnerable to RCE via parameter 'cmd'.",
            "component": keyword,
            "solution": "Update to latest version.",
            "ssvid": "MANUAL_001"
        }
        
        # Proceed to generation directly
        generator = POCGenerator()
        generated_code = generator.generate_poc(vul_info)
        
        if generated_code:
            filename = f"poc_manual_{keyword}_ai.py"
            save_path = os.path.join(os.getcwd(), filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(generated_code)
            print(f"\n💾 POC saved to: {save_path}")
            print("-" * 50)
            # print(generated_code)
            print("-" * 50)
        return

    poc_list = search_result["data"]["list"]
    total_count = search_result["data"].get("total", search_result["data"].get("count", len(poc_list)))
    print(f"\nFound {total_count} results. Showing top 5:")
    
    for idx, poc in enumerate(poc_list):
        print(f"[{idx+1}] SSVID: {poc['ssvid']} | Name: {poc['name']} | Type: {poc.get('type', 'Unknown')}")

    # 3. Select Vulnerability
    try:
        if len(sys.argv) > 2:
            selection = int(sys.argv[2]) - 1
            print(f"\n👉 Using selection from arguments: {selection + 1}")
        else:
            selection = int(input("\n👉 Select a vulnerability to generate POC for (1-5): ")) - 1
            
        if selection < 0 or selection >= len(poc_list):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return

    selected_poc = poc_list[selection]
    ssvid = selected_poc['ssvid']
    print(f"\nSelected: {selected_poc['name']} (SSVID: {ssvid})")

    # 4. Get Full Details (needed for AI context)
    print("📥 Fetching full details...")
    detail_result = client.get_poc_detail(ssvid=ssvid)
    
    vul_info = {}
    if detail_result.get("status") == "success":
        data = detail_result["data"]
        # Map Seebug fields to our simple dict
        vul_info = {
            "name": data.get("name"),
            "type": data.get("type"),
            "description": data.get("description", "No description available."),
            "component": data.get("component"),
            "solution": data.get("solution"),
            "ssvid": ssvid
        }
    else:
        print("⚠️ Failed to fetch full details. Using summary info.")
        vul_info = {
            "name": selected_poc.get("name"),
            "type": selected_poc.get("type"),
            "description": f"Vulnerability in {selected_poc.get('name')}. Type: {selected_poc.get('type')}.", # Fallback
            "ssvid": ssvid
        }

    # 5. Generate POC using AI
    generator = POCGenerator()
    generated_code = generator.generate_poc(vul_info)

    if generated_code:
        # 6. Save POC
        filename = f"poc_{ssvid}_ai.py"
        save_path = os.path.join(os.getcwd(), filename)
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
            
        print(f"\n💾 POC saved to: {save_path}")
        print("-" * 50)
        # print(generated_code)
        print("-" * 50)
        
        # Optional: Ask to run with pocsuite3 if available
        # check_cmd = "pocsuite3 --version"
        # ... (omitted for safety/complexity, just focusing on generation)
    else:
        print("❌ Failed to generate POC.")

if __name__ == "__main__":
    main()
