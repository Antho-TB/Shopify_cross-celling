import os
import shopify
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    
    session = shopify.Session(store_url, '2025-01', access_token)
    shopify.ShopifyResource.activate_session(session)

    # Collections
    c1_id = '299133730968' # Brigade forgé premium®
    c2_id = '303575662744' # Forgé Premium Evercut®
    
    p1 = shopify.Product.find(collection_id=c1_id)
    p2 = shopify.Product.find(collection_id=c2_id)
    
    target_ids = set([p.id for p in p1] + [p.id for p in p2])
    print(f"Target Product IDs ({len(target_ids)}): {target_ids}")

    # Dates
    date_min = '2025-01-22T00:00:00Z'
    date_max = '2025-07-22T23:59:59Z'
    
    print(f"Checking orders between {date_min} and {date_max}...")
    
    # Check total count first
    # IMPORTANT: Use direct shopify.Order.find with dates
    orders = shopify.Order.find(created_at_min=date_min, created_at_max=date_max, status='any', limit=250)
    print(f"Fetched {len(orders)} orders for analysis")
    
    matches = 0
    all_product_ids_seen = set()
    
    for o in orders:
        order_has_match = False
        for item in o.line_items:
            all_product_ids_seen.add(item.product_id)
            if item.product_id in target_ids:
                matches += 1
                order_has_match = True
                print(f"MATCH: Order {o.id} ({o.created_at}) contains target product {item.product_id}")
                break
    
    print(f"\nSummary of first 250 orders:")
    print(f"Orders with target products: {matches}")
    print(f"Total unique product IDs seen in these 250 orders: {len(all_product_ids_seen)}")
    
    # If no matches, maybe check a few product names to see if they SOUND premium but aren't in the collection
    if matches == 0:
        print("\nChecking if any product IDs in orders match by name (partial search)...")
        # Just sample 5 products from orders
        sample_pids = list(all_product_ids_seen)[:5]
        for pid in sample_pids:
            try:
                p = shopify.Product.find(pid)
                print(f"Order product: {p.title} (ID: {p.id}, Handle: {p.handle})")
            except:
                pass

if __name__ == "__main__":
    diagnose()
