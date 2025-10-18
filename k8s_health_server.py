#!/usr/bin/env python3
"""
Kubernetes Health Monitoring MCP Server

This MCP server provides tools to monitor Kubernetes cluster health,
including listing objects, checking pod/node status, and resource utilization.
"""

import os
import yaml
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesHealthServer:
    def __init__(self):
        self.mcp = FastMCP("Kubernetes Health Monitor")
        self.k8s_client = None
        self.k8s_apps_client = None
        self.k8s_metrics_client = None
        self.current_context = None
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.mcp.tool()
        def load_kubeconfig(kubeconfig_path: str) -> str:
            """Load a kubeconfig file and establish connection to Kubernetes clusters.
            
            Args:
                kubeconfig_path: Path to the kubeconfig file
                
            Returns:
                Success message with cluster information
            """
            try:
                # Load kubeconfig
                config.load_kube_config(config_file=kubeconfig_path)
                
                # Initialize clients
                self.k8s_client = client.CoreV1Api()
                self.k8s_apps_client = client.AppsV1Api()
                
                # Try to initialize metrics client (may not be available in all clusters)
                try:
                    self.k8s_metrics_client = client.CustomObjectsApi()
                except Exception:
                    self.k8s_metrics_client = None
                
                # Get current context
                contexts, active_context = config.list_kube_config_contexts(config_file=kubeconfig_path)
                self.current_context = active_context['name']
                
                # Test connection
                try:
                    version = self.k8s_client.get_code()
                    cluster_info = f"Connected to cluster: {self.current_context}"
                    return f"✅ {cluster_info}\nKubernetes API version: {version.git_version}"
                except Exception as e:
                    return f"❌ Failed to connect to cluster: {str(e)}"
                    
            except Exception as e:
                return f"❌ Error loading kubeconfig: {str(e)}"
        
        @self.mcp.tool()
        def list_all_objects(namespace: str = "all") -> str:
            """List all Kubernetes objects in the cluster.
            
            Args:
                namespace: Namespace to list objects from (default: "all" for all namespaces)
                
            Returns:
                JSON string containing all Kubernetes objects
            """
            if not self.k8s_client:
                return "❌ No kubeconfig loaded. Please load a kubeconfig first."
            
            try:
                objects = {}
                
                # Core V1 objects
                if namespace == "all":
                    # Pods
                    pods = self.k8s_client.list_pod_for_all_namespaces()
                    objects['pods'] = [self._pod_to_dict(pod) for pod in pods.items]
                    
                    # Services
                    services = self.k8s_client.list_service_for_all_namespaces()
                    objects['services'] = [self._service_to_dict(svc) for svc in services.items]
                    
                    # ConfigMaps
                    configmaps = self.k8s_client.list_config_map_for_all_namespaces()
                    objects['configmaps'] = [self._configmap_to_dict(cm) for cm in configmaps.items]
                    
                    # Secrets
                    secrets = self.k8s_client.list_secret_for_all_namespaces()
                    objects['secrets'] = [self._secret_to_dict(secret) for secret in secrets.items]
                    
                    # PersistentVolumes
                    pvs = self.k8s_client.list_persistent_volume()
                    objects['persistentvolumes'] = [self._pv_to_dict(pv) for pv in pvs.items]
                    
                    # Nodes
                    nodes = self.k8s_client.list_node()
                    objects['nodes'] = [self._node_to_dict(node) for node in nodes.items]
                    
                    # Namespaces
                    namespaces = self.k8s_client.list_namespace()
                    objects['namespaces'] = [self._namespace_to_dict(ns) for ns in namespaces.items]
                    
                else:
                    # Namespace-specific objects
                    pods = self.k8s_client.list_namespaced_pod(namespace)
                    objects['pods'] = [self._pod_to_dict(pod) for pod in pods.items]
                    
                    services = self.k8s_client.list_namespaced_service(namespace)
                    objects['services'] = [self._service_to_dict(svc) for svc in services.items]
                    
                    configmaps = self.k8s_client.list_namespaced_config_map(namespace)
                    objects['configmaps'] = [self._configmap_to_dict(cm) for cm in configmaps.items]
                    
                    secrets = self.k8s_client.list_namespaced_secret(namespace)
                    objects['secrets'] = [self._secret_to_dict(secret) for secret in secrets.items]
                
                # Apps V1 objects
                if namespace == "all":
                    # Deployments
                    deployments = self.k8s_apps_client.list_deployment_for_all_namespaces()
                    objects['deployments'] = [self._deployment_to_dict(deploy) for deploy in deployments.items]
                    
                    # ReplicaSets
                    replicasets = self.k8s_apps_client.list_replica_set_for_all_namespaces()
                    objects['replicasets'] = [self._replicaset_to_dict(rs) for rs in replicasets.items]
                    
                    # StatefulSets
                    statefulsets = self.k8s_apps_client.list_stateful_set_for_all_namespaces()
                    objects['statefulsets'] = [self._statefulset_to_dict(ss) for ss in statefulsets.items]
                    
                    # DaemonSets
                    daemonsets = self.k8s_apps_client.list_daemon_set_for_all_namespaces()
                    objects['daemonsets'] = [self._daemonset_to_dict(ds) for ds in daemonsets.items]
                else:
                    # Namespace-specific apps objects
                    deployments = self.k8s_apps_client.list_namespaced_deployment(namespace)
                    objects['deployments'] = [self._deployment_to_dict(deploy) for deploy in deployments.items]
                    
                    replicasets = self.k8s_apps_client.list_namespaced_replica_set(namespace)
                    objects['replicasets'] = [self._replicaset_to_dict(rs) for rs in replicasets.items]
                    
                    statefulsets = self.k8s_apps_client.list_namespaced_stateful_set(namespace)
                    objects['statefulsets'] = [self._statefulset_to_dict(ss) for ss in statefulsets.items]
                    
                    daemonsets = self.k8s_apps_client.list_namespaced_daemon_set(namespace)
                    objects['daemonsets'] = [self._daemonset_to_dict(ds) for ds in daemonsets.items]
                
                return json.dumps(objects, indent=2, default=str)
                
            except ApiException as e:
                return f"❌ Kubernetes API error: {e.reason} - {e.body}"
            except Exception as e:
                return f"❌ Error listing objects: {str(e)}"
        
        @self.mcp.tool()
        def count_objects(namespace: str = "all") -> str:
            """Count all Kubernetes objects in the cluster.
            
            Args:
                namespace: Namespace to count objects from (default: "all" for all namespaces)
                
            Returns:
                JSON string containing object counts
            """
            if not self.k8s_client:
                return "❌ No kubeconfig loaded. Please load a kubeconfig first."
            
            try:
                counts = {}
                
                if namespace == "all":
                    # Count all objects across all namespaces
                    counts['pods'] = len(self.k8s_client.list_pod_for_all_namespaces().items)
                    counts['services'] = len(self.k8s_client.list_service_for_all_namespaces().items)
                    counts['configmaps'] = len(self.k8s_client.list_config_map_for_all_namespaces().items)
                    counts['secrets'] = len(self.k8s_client.list_secret_for_all_namespaces().items)
                    counts['persistentvolumes'] = len(self.k8s_client.list_persistent_volume().items)
                    counts['nodes'] = len(self.k8s_client.list_node().items)
                    counts['namespaces'] = len(self.k8s_client.list_namespace().items)
                    counts['deployments'] = len(self.k8s_apps_client.list_deployment_for_all_namespaces().items)
                    counts['replicasets'] = len(self.k8s_apps_client.list_replica_set_for_all_namespaces().items)
                    counts['statefulsets'] = len(self.k8s_apps_client.list_stateful_set_for_all_namespaces().items)
                    counts['daemonsets'] = len(self.k8s_apps_client.list_daemon_set_for_all_namespaces().items)
                else:
                    # Count objects in specific namespace
                    counts['pods'] = len(self.k8s_client.list_namespaced_pod(namespace).items)
                    counts['services'] = len(self.k8s_client.list_namespaced_service(namespace).items)
                    counts['configmaps'] = len(self.k8s_client.list_namespaced_config_map(namespace).items)
                    counts['secrets'] = len(self.k8s_client.list_namespaced_secret(namespace).items)
                    counts['deployments'] = len(self.k8s_apps_client.list_namespaced_deployment(namespace).items)
                    counts['replicasets'] = len(self.k8s_apps_client.list_namespaced_replica_set(namespace).items)
                    counts['statefulsets'] = len(self.k8s_apps_client.list_namespaced_stateful_set(namespace).items)
                    counts['daemonsets'] = len(self.k8s_apps_client.list_namespaced_daemon_set(namespace).items)
                
                return json.dumps(counts, indent=2)
                
            except ApiException as e:
                return f"❌ Kubernetes API error: {e.reason} - {e.body}"
            except Exception as e:
                return f"❌ Error counting objects: {str(e)}"
        
        @self.mcp.tool()
        def get_pod_health(namespace: str = "all", pod_name: str = None) -> str:
            """Get health status and resource utilization of pods.
            
            Args:
                namespace: Namespace to check pods in (default: "all" for all namespaces)
                pod_name: Specific pod name to check (optional)
                
            Returns:
                JSON string containing pod health information
            """
            if not self.k8s_client:
                return "❌ No kubeconfig loaded. Please load a kubeconfig first."
            
            try:
                pod_health = []
                
                if pod_name and namespace != "all":
                    # Get specific pod
                    pod = self.k8s_client.read_namespaced_pod(pod_name, namespace)
                    pod_health.append(self._get_pod_health_info(pod))
                else:
                    # Get all pods
                    if namespace == "all":
                        pods = self.k8s_client.list_pod_for_all_namespaces()
                    else:
                        pods = self.k8s_client.list_namespaced_pod(namespace)
                    
                    for pod in pods.items:
                        if pod_name is None or pod.metadata.name == pod_name:
                            pod_health.append(self._get_pod_health_info(pod))
                
                return json.dumps(pod_health, indent=2, default=str)
                
            except ApiException as e:
                return f"❌ Kubernetes API error: {e.reason} - {e.body}"
            except Exception as e:
                return f"❌ Error getting pod health: {str(e)}"
        
        @self.mcp.tool()
        def get_node_health() -> str:
            """Get health status and resource utilization of nodes.
            
            Returns:
                JSON string containing node health information
            """
            if not self.k8s_client:
                return "❌ No kubeconfig loaded. Please load a kubeconfig first."
            
            try:
                nodes = self.k8s_client.list_node()
                node_health = []
                
                for node in nodes.items:
                    node_health.append(self._get_node_health_info(node))
                
                return json.dumps(node_health, indent=2, default=str)
                
            except ApiException as e:
                return f"❌ Kubernetes API error: {e.reason} - {e.body}"
            except Exception as e:
                return f"❌ Error getting node health: {str(e)}"
    
    def _get_pod_health_info(self, pod) -> Dict[str, Any]:
        """Extract health information from a pod object"""
        health_info = {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'phase': pod.status.phase,
            'ready': self._is_pod_ready(pod),
            'restart_count': sum(container.restart_count for container in pod.status.container_statuses or []),
            'creation_timestamp': pod.metadata.creation_timestamp,
            'labels': pod.metadata.labels or {},
            'node_name': pod.spec.node_name,
            'containers': []
        }
        
        # Container information
        for container in pod.spec.containers:
            container_info = {
                'name': container.name,
                'image': container.image,
                'resources': {
                    'requests': container.resources.requests or {},
                    'limits': container.resources.limits or {}
                }
            }
            
            # Container status
            if pod.status.container_statuses:
                for status in pod.status.container_statuses:
                    if status.name == container.name:
                        container_info['status'] = {
                            'ready': status.ready,
                            'restart_count': status.restart_count,
                            'state': self._get_container_state(status.state)
                        }
                        break
            
            health_info['containers'].append(container_info)
        
        # Try to get resource metrics if metrics server is available
        if self.k8s_metrics_client:
            try:
                metrics = self._get_pod_metrics(pod.metadata.name, pod.metadata.namespace)
                health_info['metrics'] = metrics
            except Exception:
                health_info['metrics'] = None
        
        return health_info
    
    def _get_node_health_info(self, node) -> Dict[str, Any]:
        """Extract health information from a node object"""
        health_info = {
            'name': node.metadata.name,
            'ready': self._is_node_ready(node),
            'creation_timestamp': node.metadata.creation_timestamp,
            'labels': node.metadata.labels or {},
            'taints': [self._taint_to_dict(taint) for taint in node.spec.taints or []],
            'capacity': node.status.capacity or {},
            'allocatable': node.status.allocatable or {},
            'conditions': [self._condition_to_dict(condition) for condition in node.status.conditions or []],
            'node_info': {
                'architecture': node.status.node_info.architecture,
                'kernel_version': node.status.node_info.kernel_version,
                'kubelet_version': node.status.node_info.kubelet_version,
                'operating_system': node.status.node_info.operating_system,
                'os_image': node.status.node_info.os_image
            }
        }
        
        # Try to get resource metrics if metrics server is available
        if self.k8s_metrics_client:
            try:
                metrics = self._get_node_metrics(node.metadata.name)
                health_info['metrics'] = metrics
            except Exception:
                health_info['metrics'] = None
        
        return health_info
    
    def _get_pod_metrics(self, pod_name: str, namespace: str) -> Optional[Dict[str, Any]]:
        """Get pod resource metrics from metrics server"""
        try:
            metrics = self.k8s_metrics_client.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                name=pod_name
            )
            
            containers_metrics = []
            for container in metrics.get('containers', []):
                containers_metrics.append({
                    'name': container['name'],
                    'usage': container.get('usage', {})
                })
            
            return {
                'timestamp': metrics.get('timestamp'),
                'window': metrics.get('window'),
                'containers': containers_metrics
            }
        except Exception:
            return None
    
    def _get_node_metrics(self, node_name: str) -> Optional[Dict[str, Any]]:
        """Get node resource metrics from metrics server"""
        try:
            metrics = self.k8s_metrics_client.get_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
                name=node_name
            )
            
            return {
                'timestamp': metrics.get('timestamp'),
                'window': metrics.get('window'),
                'usage': metrics.get('usage', {})
            }
        except Exception:
            return None
    
    def _is_pod_ready(self, pod) -> bool:
        """Check if pod is ready"""
        if not pod.status.conditions:
            return False
        
        for condition in pod.status.conditions:
            if condition.type == "Ready":
                return condition.status == "True"
        return False
    
    def _is_node_ready(self, node) -> bool:
        """Check if node is ready"""
        if not node.status.conditions:
            return False
        
        for condition in node.status.conditions:
            if condition.type == "Ready":
                return condition.status == "True"
        return False
    
    def _get_container_state(self, state) -> str:
        """Get container state as string"""
        if state.running:
            return "Running"
        elif state.waiting:
            return f"Waiting: {state.waiting.reason}"
        elif state.terminated:
            return f"Terminated: {state.terminated.reason}"
        else:
            return "Unknown"
    
    def _taint_to_dict(self, taint) -> Dict[str, str]:
        """Convert taint to dictionary"""
        return {
            'key': taint.key,
            'value': taint.value or '',
            'effect': taint.effect
        }
    
    def _condition_to_dict(self, condition) -> Dict[str, Any]:
        """Convert condition to dictionary"""
        return {
            'type': condition.type,
            'status': condition.status,
            'reason': condition.reason or '',
            'message': condition.message or '',
            'last_transition_time': condition.last_transition_time
        }
    
    # Object conversion methods
    def _pod_to_dict(self, pod) -> Dict[str, Any]:
        return {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'phase': pod.status.phase,
            'ready': self._is_pod_ready(pod),
            'node_name': pod.spec.node_name,
            'creation_timestamp': pod.metadata.creation_timestamp
        }
    
    def _service_to_dict(self, service) -> Dict[str, Any]:
        return {
            'name': service.metadata.name,
            'namespace': service.metadata.namespace,
            'type': service.spec.type,
            'cluster_ip': service.spec.cluster_ip,
            'ports': [{'port': port.port, 'target_port': port.target_port, 'protocol': port.protocol} for port in service.spec.ports or []],
            'creation_timestamp': service.metadata.creation_timestamp
        }
    
    def _configmap_to_dict(self, configmap) -> Dict[str, Any]:
        return {
            'name': configmap.metadata.name,
            'namespace': configmap.metadata.namespace,
            'data_keys': list(configmap.data.keys()) if configmap.data else [],
            'creation_timestamp': configmap.metadata.creation_timestamp
        }
    
    def _secret_to_dict(self, secret) -> Dict[str, Any]:
        return {
            'name': secret.metadata.name,
            'namespace': secret.metadata.namespace,
            'type': secret.type,
            'data_keys': list(secret.data.keys()) if secret.data else [],
            'creation_timestamp': secret.metadata.creation_timestamp
        }
    
    def _pv_to_dict(self, pv) -> Dict[str, Any]:
        return {
            'name': pv.metadata.name,
            'capacity': pv.spec.capacity,
            'access_modes': pv.spec.access_modes,
            'reclaim_policy': pv.spec.persistent_volume_reclaim_policy,
            'status': pv.status.phase,
            'creation_timestamp': pv.metadata.creation_timestamp
        }
    
    def _node_to_dict(self, node) -> Dict[str, Any]:
        return {
            'name': node.metadata.name,
            'ready': self._is_node_ready(node),
            'capacity': node.status.capacity,
            'allocatable': node.status.allocatable,
            'creation_timestamp': node.metadata.creation_timestamp
        }
    
    def _namespace_to_dict(self, namespace) -> Dict[str, Any]:
        return {
            'name': namespace.metadata.name,
            'status': namespace.status.phase,
            'creation_timestamp': namespace.metadata.creation_timestamp
        }
    
    def _deployment_to_dict(self, deployment) -> Dict[str, Any]:
        return {
            'name': deployment.metadata.name,
            'namespace': deployment.metadata.namespace,
            'replicas': deployment.spec.replicas,
            'ready_replicas': deployment.status.ready_replicas or 0,
            'available_replicas': deployment.status.available_replicas or 0,
            'creation_timestamp': deployment.metadata.creation_timestamp
        }
    
    def _replicaset_to_dict(self, replicaset) -> Dict[str, Any]:
        return {
            'name': replicaset.metadata.name,
            'namespace': replicaset.metadata.namespace,
            'replicas': replicaset.spec.replicas,
            'ready_replicas': replicaset.status.ready_replicas or 0,
            'available_replicas': replicaset.status.available_replicas or 0,
            'creation_timestamp': replicaset.metadata.creation_timestamp
        }
    
    def _statefulset_to_dict(self, statefulset) -> Dict[str, Any]:
        return {
            'name': statefulset.metadata.name,
            'namespace': statefulset.metadata.namespace,
            'replicas': statefulset.spec.replicas,
            'ready_replicas': statefulset.status.ready_replicas or 0,
            'current_replicas': statefulset.status.current_replicas or 0,
            'creation_timestamp': statefulset.metadata.creation_timestamp
        }
    
    def _daemonset_to_dict(self, daemonset) -> Dict[str, Any]:
        return {
            'name': daemonset.metadata.name,
            'namespace': daemonset.metadata.namespace,
            'desired_number_scheduled': daemonset.status.desired_number_scheduled or 0,
            'current_number_scheduled': daemonset.status.current_number_scheduled or 0,
            'number_ready': daemonset.status.number_ready or 0,
            'creation_timestamp': daemonset.metadata.creation_timestamp
        }
    
    def run(self, port: int = 8000, transport: str = 'http'):
        """Run the MCP server"""
        print(f"🚀 Starting Kubernetes Health MCP Server...")
        print(f"📍 Server URL: http://localhost:{port}/mcp")
        print(f"🔌 Transport: {transport}")
        #print(f"🛠️  Available tools: {len(self.mcp.get_tools().keys())}")
        print(f"🛠️  Available tools: {self.mcp.get_tools()}")
        print("=" * 50)
        self.mcp.run(transport=transport, port=port)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', 
        type=int, 
        default=8000,
        help='Port to run the MCP server on (default: 8000)'
    )
    
    parser.add_argument(
        '--transport', 
        type=str, 
        default='http',
        choices=['http', 'stdio'],
        help='Transport method for the MCP server (default: http)'
    )
    
    args = parser.parse_args()
    
    # Create and run the server
    server = KubernetesHealthServer()
    server.run(port=args.port, transport=args.transport)


if __name__ == "__main__":
    main()
