from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch

app = Flask(__name__)

# Connect to your Elasticsearch instance
es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}], basic_auth=('elastic', 'CbIxwM6z85Dm6fKtAJte'))
index_name = "reuters" 
@app.route("/")
def index():
    return render_template("autocomplete.html")

def autocomplete_query(index_name, user_input, size=10):
    # Elasticsearch query for autocomplete
    body = {
        "query": {
            "match": {
                "title": {
                    "query": user_input,
                    "fuzziness": "AUTO"
                }
            }
        }
    }

    # Execute the query
    result = es.search(index=index_name, body=body, size=size)
    hits = result["hits"]["hits"]

    return hits


@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    user_input = request.args.get("user_input")
    autocomplete_results = autocomplete_query(index_name, user_input)
    response_data = [{"title": hit["_source"]["title"], "data": hit["_source"]} for hit in autocomplete_results]
    return jsonify(response_data)

def search_documents(query, temporal_expression, georeference, index_name):
    search_query = {
       "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title.autocomplete^3", "content"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "boost": 3
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "nested": {
                                        "path": "temporal_expressions",
                                        "query": {
                                            "match": {
                                                "temporal_expressions.expression": temporal_expression
                                            }
                                        }
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "georeferences",
                                        "query": {
                                            "match": {
                                                "georeferences.expression": georeference
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "sort": [
           
            {
                "_score": {
                    "order": "desc"
                }
            }
        ]
    }
    
    results = es.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in results["hits"]["hits"]]


@app.route('/search_page')
def search_page():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    temporal_expression = request.json.get('temporal_expression')
    georeference = request.json.get('georeference')
    index_name = "reuters" 

    results = search_documents(query, temporal_expression, georeference, index_name)

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)