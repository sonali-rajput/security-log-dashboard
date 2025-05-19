from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
import json
from datetime import datetime

app = Flask(__name__)

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Get total logs count
    try:
        total_logs = es.count(index='security-logs')['count']
    except Exception as e:
        print(f"Error getting total logs: {str(e)}")
        total_logs = 0
    
    # Count errors
    try:
        error_query = {"query": {"term": {"is_error": 1}}}
        error_count = es.count(index='security-logs', body=error_query)['count']
    except Exception as e:
        print(f"Error getting error count: {str(e)}")
        error_count = 0
    
    # Count potential attacks
    try:
        attack_query = {"query": {"term": {"is_potential_attack": 1}}}
        attack_count = es.count(index='security-logs', body=attack_query)['count']
    except Exception as e:
        print(f"Error getting attack count: {str(e)}")
        attack_count = 0
    
    # Get top IPs
    try:
        top_ips_query = {
            "size": 0,
            "aggs": {
                "top_ips": {
                    "terms": {
                        "field": "ip",
                        "size": 10
                    }
                }
            }
        }
        top_ips_result = es.search(index='security-logs', body=top_ips_query)
        top_ips = top_ips_result['aggregations']['top_ips']['buckets']
    except Exception as e:
        print(f"Error getting top IPs: {str(e)}")
        top_ips = []
    
    # Get status code distribution
    try:
        status_query = {
            "size": 0,
            "aggs": {
                "status_codes": {
                    "terms": {
                        "field": "status_code",
                        "size": 10
                    }
                }
            }
        }
        status_result = es.search(index='security-logs', body=status_query)
        status_codes = status_result['aggregations']['status_codes']['buckets']
    except Exception as e:
        print(f"Error getting status codes: {str(e)}")
        status_codes = []
    
    return render_template(
        'dashboard.html', 
        total_logs=total_logs,
        error_count=error_count,
        attack_count=attack_count,
        top_ips=top_ips,
        status_codes=status_codes
    )

@app.route('/search')
def search():
    query = request.args.get('q', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Default to empty results
    results = {"hits": {"hits": []}}
    
    if query or from_date or to_date:
        # Build Elasticsearch query
        es_query = {"query": {"bool": {"must": []}}}
        
        if query:
            es_query['query']['bool']['must'].append(
                {"query_string": {"query": query}}
            )
        
        if from_date and to_date:
            es_query['query']['bool']['must'].append(
                {"range": {"timestamp_parsed": {"gte": from_date, "lte": to_date}}}
            )
        
        try:
            results = es.search(index='security-logs', body=es_query, size=100)
        except Exception as e:
            print(f"Error searching logs: {str(e)}")
    
    return render_template('search.html', query=query, results=results['hits']['hits'])

@app.route('/api/logs/timeline')
def logs_timeline():
    # Query for logs over time
    timeline_query = {
        "size": 0,
        "aggs": {
            "logs_over_time": {
                "date_histogram": {
                    "field": "timestamp_parsed",
                    "calendar_interval": "hour"
                }
            }
        }
    }
    
    try:
        results = es.search(index='security-logs', body=timeline_query)
        buckets = results['aggregations']['logs_over_time']['buckets']
        
        timeline_data = [
            {"time": bucket['key_as_string'], "count": bucket['doc_count']}
            for bucket in buckets
        ]
    except Exception as e:
        print(f"Error getting timeline data: {str(e)}")
        timeline_data = []
    
    return jsonify(timeline_data)

@app.route('/api/logs/errors_timeline')
def errors_timeline():
    # Query for errors over time
    error_timeline_query = {
        "size": 0,
        "query": {
            "term": {"is_error": 1}
        },
        "aggs": {
            "errors_over_time": {
                "date_histogram": {
                    "field": "timestamp_parsed",
                    "calendar_interval": "hour"
                }
            }
        }
    }
    
    try:
        results = es.search(index='security-logs', body=error_timeline_query)
        buckets = results['aggregations']['errors_over_time']['buckets']
        
        timeline_data = [
            {"time": bucket['key_as_string'], "count": bucket['doc_count']}
            for bucket in buckets
        ]
    except Exception as e:
        print(f"Error getting errors timeline: {str(e)}")
        timeline_data = []
    
    return jsonify(timeline_data)

@app.route('/api/logs/attack_types')
def attack_types():
    # Get data for potential attacks by type
    query = {
        "size": 0,
        "query": {
            "term": {"is_potential_attack": 1}
        },
        "aggs": {
            "endpoint_patterns": {
                "terms": {
                    "field": "endpoint.keyword",
                    "size": 10
                }
            }
        }
    }
    
    try:
        results = es.search(index='security-logs', body=query)
        buckets = results['aggregations']['endpoint_patterns']['buckets']
        
        attack_data = [
            {"pattern": bucket['key'], "count": bucket['doc_count']}
            for bucket in buckets
        ]
    except Exception as e:
        print(f"Error getting attack types: {str(e)}")
        attack_data = []
    
    return jsonify(attack_data)

@app.route('/api/logs/top_ips')
def top_ips_api():
    try:
        # Get top IPs
        top_ips_query = {
            "size": 0,
            "aggs": {
                "top_ips": {
                    "terms": {
                        "field": "ip",
                        "size": 10
                    }
                }
            }
        }
        top_ips_result = es.search(index='security-logs', body=top_ips_query)
        top_ips = top_ips_result['aggregations']['top_ips']['buckets']
        return jsonify([{"ip": item["key"], "count": item["doc_count"]} for item in top_ips])
    except Exception as e:
        print(f"Error getting top IPs: {str(e)}")
        return jsonify([])

@app.route('/api/logs/status_codes')
def status_codes_api():
    try:
        # Get status code distribution
        status_query = {
            "size": 0,
            "aggs": {
                "status_codes": {
                    "terms": {
                        "field": "status_code",
                        "size": 10
                    }
                }
            }
        }
        status_result = es.search(index='security-logs', body=status_query)
        status_codes = status_result['aggregations']['status_codes']['buckets']
        return jsonify([{"status": item["key"], "count": item["doc_count"]} for item in status_codes])
    except Exception as e:
        print(f"Error getting status codes: {str(e)}")
        return jsonify([])

@app.route('/debug')
def debug():
    """
    Debug endpoint to check Elasticsearch connection and index info
    """
    debug_info = {
        "elasticsearch_status": "Unknown",
        "indices": [],
        "security_logs_count": 0,
        "security_logs_mappings": {},
        "sample_document": None
    }
    
    try:
        # Check ES status
        es_info = es.info()
        debug_info["elasticsearch_status"] = "Connected"
        debug_info["elasticsearch_version"] = es_info["version"]["number"]
        
        # Get indices
        indices = es.indices.get_alias("*")
        debug_info["indices"] = list(indices.keys())
        
        # Get count of security-logs
        if 'security-logs' in indices:
            count = es.count(index='security-logs')
            debug_info["security_logs_count"] = count["count"]
            
            # Get mappings
            mappings = es.indices.get_mapping(index='security-logs')
            debug_info["security_logs_mappings"] = mappings
            
            # Get a sample document
            if count["count"] > 0:
                sample = es.search(index='security-logs', size=1)
                debug_info["sample_document"] = sample["hits"]["hits"][0]["_source"] if sample["hits"]["hits"] else None
    except Exception as e:
        debug_info["elasticsearch_status"] = f"Error: {str(e)}"
    
    return jsonify(debug_info)

if __name__ == '__main__':
    app.run(debug=True)