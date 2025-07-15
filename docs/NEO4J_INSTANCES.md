# Neo4j Instance Configuration

The MCP Knowledge Graph system now supports both local and remote Neo4j instances.

## Configuration

The `config.yaml` file has been updated to include separate configurations for local and remote Neo4j instances:

```yaml
neo4j:
  local:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "mcpservers"
  remote:
    uri: "bolt://your-remote-host:7687"  # Update with your remote Neo4j instance
    user: "neo4j"
    password: "your-remote-password"     # Update with your remote password
```

## Usage

All data loading scripts now support `--local` and `--remote` flags:

### Main Script
```bash
# Use local Neo4j (default)
python main.py --local

# Use remote Neo4j
python main.py --remote

# Local is the default, so this is equivalent to --local
python main.py
```

### Full Deduplication Script
```bash
# Load to local Neo4j (default)
python run_full_deduplication.py --local

# Load to remote Neo4j
python run_full_deduplication.py --remote
```

### Sample Deduplication Script
```bash
# Test with local Neo4j (default)
python run_sample_deduplication.py --local

# Test with remote Neo4j
python run_sample_deduplication.py --remote
```

## Setting Up Remote Neo4j

1. **Update Configuration**: Edit `config.yaml` and update the remote section:
   ```yaml
   neo4j:
     remote:
       uri: "bolt://your-remote-host:7687"
       user: "your-username"
       password: "your-password"
   ```

2. **Test Connection**: Use the test script to verify configuration:
   ```bash
   python test_config.py
   ```

3. **Run with Remote**: Use the `--remote` flag with any script:
   ```bash
   python run_full_deduplication.py --remote
   ```

## Examples

### Load to Local Neo4j (Default)
```bash
# These are all equivalent
python run_full_deduplication.py
python run_full_deduplication.py --local
```

### Load to Remote Neo4j
```bash
python run_full_deduplication.py --remote
```

### Build Complete Knowledge Graph on Remote
```bash
python main.py --clear-neo4j --remote
```

## Benefits

- **Development vs Production**: Use local for development/testing, remote for production
- **Scalability**: Remote instances can be more powerful for large datasets
- **Team Collaboration**: Multiple developers can share a remote instance
- **Backup/Recovery**: Remote instances can have better backup strategies

## Testing

Use `test_config.py` to verify both configurations are properly loaded:

```bash
python test_config.py
```

This will show both local and remote configurations and test that the Neo4jManager can initialize with both.