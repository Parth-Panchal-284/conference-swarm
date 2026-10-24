from dotenv import load_dotenv
from brightdata import SyncBrightDataClient


load_dotenv()


with SyncBrightDataClient(
    auto_create_zones=True
) as client:
    result = client.search.google(
        query=(
            '"Patch the Conference" hackathon '
            'AI agents FalkorDB Bright Data'
        ),
        num_results=5,
    )

    print("Success:", result.success)

    for item in result.data:
        print("\nTITLE:")
        print(item.get("title"))

        print("URL:")
        print(
            item.get("url")
            or item.get("link")
        )

        print("DESCRIPTION:")
        print(item.get("description"))
