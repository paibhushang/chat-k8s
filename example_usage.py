#!/usr/bin/env python3
"""
Example usage of the Kubernetes Health Monitoring MCP Server

This script demonstrates how to use the MCP server tools to monitor
Kubernetes cluster health.

Usage:
    uv run python example_usage.py
    # or
    source .venv/bin/activate
    python example_usage.py
"""

import json
from k8s_health_server import KubernetesHealthServer

def main():
    # Initialize the server
    server = KubernetesHealthServer()
    
    # Example kubeconfig path (update this to your actual path)
    kubeconfig_path = "/path/to/your/kubeconfig"
    
    print("🚀 Kubernetes Health Monitoring Example")
    print("=" * 50)
    
    # 1. Load kubeconfig
    print("\n1. Loading kubeconfig...")
    result = server.mcp.tools['load_kubeconfig'](kubeconfig_path)
    print(result)
    
    if "❌" in result:
        print("❌ Failed to load kubeconfig. Please check the path and try again.")
        return
    
    # 2. Count all objects
    print("\n2. Counting all objects in the cluster...")
    counts = server.mcp.tools['count_objects']("all")
    print("Object counts:")
    print(json.dumps(json.loads(counts), indent=2))
    
    # 3. List objects in default namespace
    print("\n3. Listing objects in default namespace...")
    objects = server.mcp.tools['list_all_objects']("default")
    objects_data = json.loads(objects)
    
    print(f"Found {len(objects_data.get('pods', []))} pods")
    print(f"Found {len(objects_data.get('services', []))} services")
    print(f"Found {len(objects_data.get('deployments', []))} deployments")
    
    # 4. Get pod health
    print("\n4. Getting pod health information...")
    pod_health = server.mcp.tools['get_pod_health']("all")
    pod_data = json.loads(pod_health)
    
    print(f"Found {len(pod_data)} pods")
    for pod in pod_data[:3]:  # Show first 3 pods
        print(f"  - {pod['name']} ({pod['namespace']}): {pod['phase']} - Ready: {pod['ready']}")
    
    # 5. Get node health
    print("\n5. Getting node health information...")
    node_health = server.mcp.tools['get_node_health']()
    node_data = json.loads(node_health)
    
    print(f"Found {len(node_data)} nodes")
    for node in node_data:
        print(f"  - {node['name']}: Ready: {node['ready']}")
        if node.get('capacity'):
            cpu = node['capacity'].get('cpu', 'Unknown')
            memory = node['capacity'].get('memory', 'Unknown')
            print(f"    Capacity: CPU={cpu}, Memory={memory}")
    
    print("\n✅ Example completed successfully!")

if __name__ == "__main__":
    main()
