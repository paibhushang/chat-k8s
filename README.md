# Kubernetes Health Monitoring MCP Server

An MCP (Model Context Protocol) server that provides comprehensive Kubernetes cluster health monitoring capabilities. This server allows you to connect to Kubernetes clusters using kubeconfig files and monitor the health, status, and resource utilization of your applications and infrastructure.

## Quick Start

**Server Connection:**
- **URL**: `http://localhost:8000/mcp`
- **Port**: `8000`
- **Start Server**: `uv run python k8s_health_server.py`

## Features

- **Cluster Connection**: Load and connect to Kubernetes clusters using kubeconfig files
- **Object Listing**: List all Kubernetes objects across namespaces or specific namespaces
- **Object Counting**: Get counts of all Kubernetes object types
- **Pod Health Monitoring**: Check pod status, readiness, restart counts, and resource utilization
- **Node Health Monitoring**: Monitor node status, capacity, and resource utilization
- **Resource Metrics**: Integration with Kubernetes Metrics Server for CPU and memory usage data

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- A valid kubeconfig file with access to your Kubernetes cluster(s)

### Install uv

If you don't have `uv` installed, install it first:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Install Dependencies

1. Install the project and its dependencies:
```bash
uv sync
```

2. Or install in development mode with dev dependencies:
```bash
uv sync --dev
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

## Usage

### Starting the Server

```bash
# Using uv run (recommended) - default port 8000
uv run python k8s_health_server.py

# Or activate the virtual environment first
source .venv/bin/activate
python k8s_health_server.py

# Run on a custom port
uv run python k8s_health_server.py --port 9000

# Use stdio transport
uv run python k8s_health_server.py --transport stdio

# Custom port and transport
uv run python k8s_health_server.py --port 9000 --transport http
```

### Connecting to the MCP Server

Once the server is running, it will be available at:

- **URL**: `http://localhost:8000/mcp`
- **Port**: `8000`
- **Transport**: HTTP

The server uses the standard MCP (Model Context Protocol) over HTTP transport. You can connect to it using any MCP-compatible client or tool that supports HTTP transport.

#### Connection Examples

**Using MCP Client:**
```bash
# Connect to the server
mcp connect http://localhost:8000/mcp
```

**Using curl for testing:**
```bash
# Test server health
curl http://localhost:8000/mcp/health

# List available tools
curl http://localhost:8000/mcp/tools
```

**Command Line Arguments:**
- `--port`: Port number to run the server on (default: 8000)
- `--transport`: Transport method - 'http' or 'stdio' (default: http)

**Help and Options:**
```bash
# Show help and available options
uv run python k8s_health_server.py --help
```

#### Troubleshooting Connection Issues

**Check if the server is running:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Or on Windows
netstat -an | findstr :8000
```

**Test server connectivity:**
```bash
# Test basic connectivity
curl -v http://localhost:8000/mcp

# Check server health (if health endpoint is available)
curl http://localhost:8000/mcp/health
```

**Common Issues:**
- **Port already in use**: Change the port using `--port 9000`
- **Permission denied**: Make sure you have permission to bind to the port
- **Firewall blocking**: Check if your firewall allows connections on the specified port
- **Wrong URL**: Ensure you're using the correct URL format: `http://localhost:8000/mcp`
- **Transport mismatch**: Use `--transport stdio` for stdio-based clients

### Available Tools

#### 1. Load Kubeconfig
```python
load_kubeconfig(kubeconfig_path: str) -> str
```
Load a kubeconfig file and establish connection to Kubernetes clusters.

**Parameters:**
- `kubeconfig_path`: Path to the kubeconfig file

**Returns:** Success message with cluster information

#### 2. List All Objects
```python
list_all_objects(namespace: str = "all") -> str
```
List all Kubernetes objects in the cluster.

**Parameters:**
- `namespace`: Namespace to list objects from (default: "all" for all namespaces)

**Returns:** JSON string containing all Kubernetes objects

#### 3. Count Objects
```python
count_objects(namespace: str = "all") -> str
```
Count all Kubernetes objects in the cluster.

**Parameters:**
- `namespace`: Namespace to count objects from (default: "all" for all namespaces)

**Returns:** JSON string containing object counts

#### 4. Get Pod Health
```python
get_pod_health(namespace: str = "all", pod_name: str = None) -> str
```
Get health status and resource utilization of pods.

**Parameters:**
- `namespace`: Namespace to check pods in (default: "all" for all namespaces)
- `pod_name`: Specific pod name to check (optional)

**Returns:** JSON string containing pod health information

#### 5. Get Node Health
```python
get_node_health() -> str
```
Get health status and resource utilization of nodes.

**Returns:** JSON string containing node health information

## Object Types Supported

The server can list and count the following Kubernetes object types:

### Core V1 Objects
- Pods
- Services
- ConfigMaps
- Secrets
- PersistentVolumes
- Nodes
- Namespaces

### Apps V1 Objects
- Deployments
- ReplicaSets
- StatefulSets
- DaemonSets

## Health Information Provided

### Pod Health
- Pod phase and readiness status
- Container status and restart counts
- Resource requests and limits
- CPU and memory utilization (if metrics server is available)
- Node assignment
- Creation timestamp and labels

### Node Health
- Node readiness status
- Resource capacity and allocatable resources
- Node conditions and taints
- System information (architecture, kernel version, etc.)
- CPU and memory utilization (if metrics server is available)

## Prerequisites

- Python 3.8+
- uv package manager
- Valid kubeconfig file with cluster access
- Kubernetes cluster with appropriate RBAC permissions
- (Optional) Kubernetes Metrics Server for resource utilization data

## Error Handling

The server includes comprehensive error handling for:
- Invalid kubeconfig files
- Network connectivity issues
- Kubernetes API errors
- Missing RBAC permissions
- Metrics server unavailability

## Security Notes

- The server requires appropriate RBAC permissions to read cluster resources
- Kubeconfig files should be kept secure and not shared
- Consider using service accounts with minimal required permissions

## Example Usage

### Running the Example

```bash
# Run the example script
uv run python example_usage.py

# Or with the virtual environment activated
source .venv/bin/activate
python example_usage.py
```

### Server Command Line Options

```bash
# Show all available options
uv run python k8s_health_server.py --help

# Available options:
# --port PORT        Port to run the MCP server on (default: 8000)
# --transport {http,stdio}  Transport method (default: http)
```

### Programmatic Usage

```python
# Load kubeconfig
result = load_kubeconfig("/path/to/kubeconfig")

# List all objects in default namespace
objects = list_all_objects("default")

# Count all objects across all namespaces
counts = count_objects("all")

# Get health of all pods
pod_health = get_pod_health()

# Get health of a specific pod
specific_pod = get_pod_health("default", "my-pod")

# Get node health
node_health = get_node_health()
```

## Development

### Setting up Development Environment

```bash
# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy k8s_health_server.py

# Linting
uv run flake8 k8s_health_server.py
```

## License

This project is open source and available under the MIT License.
