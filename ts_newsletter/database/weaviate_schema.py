"""
Weaviate schema initialization
Vector database schema for semantic search and deduplication
"""

import weaviate
from weaviate.classes.config import Configure, DataType, Property


def create_weaviate_schema(client: weaviate.WeaviateClient):
    """
    Create Weaviate schema for article embeddings

    Args:
        client: Weaviate client instance
    """

    # Article collection for semantic search
    article_schema = {
        "class": "Article",
        "description": "Articles about advertising fraud and security threats",
        "vectorizer": "none",  # We'll provide our own embeddings from OpenAI
        "properties": [
            {
                "name": "article_id",
                "dataType": ["text"],
                "description": "UUID from PostgreSQL articles table"
            },
            {
                "name": "url",
                "dataType": ["text"],
                "description": "Article URL"
            },
            {
                "name": "title",
                "dataType": ["text"],
                "description": "Article title"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Full article content"
            },
            {
                "name": "snippet",
                "dataType": ["text"],
                "description": "Brief article snippet"
            },
            {
                "name": "source",
                "dataType": ["text"],
                "description": "Source publication name"
            },
            {
                "name": "published_date",
                "dataType": ["date"],
                "description": "Publication date"
            },
            {
                "name": "collected_date",
                "dataType": ["date"],
                "description": "Collection date"
            },
            {
                "name": "threat_type",
                "dataType": ["text"],
                "description": "Type of threat (if analyzed)"
            },
            {
                "name": "tags",
                "dataType": ["text[]"],
                "description": "Tags/categories"
            },
            {
                "name": "priority_level",
                "dataType": ["text"],
                "description": "Priority level: HIGH, MEDIUM, LOW"
            },
            {
                "name": "overall_score",
                "dataType": ["number"],
                "description": "Overall relevance score (0-10)"
            }
        ]
    }

    # Check if collection exists
    try:
        client.collections.delete("Article")
        print("Deleted existing Article collection")
    except:
        pass

    # Create collection
    client.collections.create_from_dict(article_schema)
    print("Created Article collection")


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Connect to Weaviate
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080
    )

    try:
        # Create schema
        create_weaviate_schema(client)
        print("Weaviate schema created successfully")

        # Test query
        articles = client.collections.get("Article")
        print(f"Article collection ready: {articles}")

    finally:
        client.close()
