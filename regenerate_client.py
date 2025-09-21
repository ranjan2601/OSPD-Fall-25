#!/usr/bin/env python3
"""Script to regenerate the auto-generated client from OpenAPI schema.

This script demonstrates how to regenerate the client code without
needing a running service instance.
"""

import json
import subprocess
import sys
from pathlib import Path


def regenerate_client() -> None:
    """Regenerate the auto-generated client from schema."""
    
    service_client_dir = Path("src/mail_client_service_client")
    schema_file = service_client_dir / "openapi_schema.json"
    generated_dir = service_client_dir / "src" / "mail_client_service_client" / "generated"
    
    if not schema_file.exists():
        print(f"Error: Schema file not found at {schema_file}")
        sys.exit(1)
    
    print("Validating OpenAPI schema...")
    try:
        with schema_file.open() as f:
            schema = json.load(f)
        print(f"Schema validation passed: {schema['info']['title']} v{schema['info']['version']}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required field in schema: {e}")
        sys.exit(1)
    
    if generated_dir.exists():
        print(f"Removing existing generated directory: {generated_dir}")
        import shutil
        shutil.rmtree(generated_dir)
    
    print("Generating client code...")
    try:
        cmd = [
            "openapi-python-client",
            "generate",
            "--path", str(schema_file),
            "--output-path", str(generated_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error generating client: {result.stderr}")
            sys.exit(1)
            
        print("Client code generated successfully!")
        print(f"Output directory: {generated_dir}")
        
        generated_client_dir = generated_dir / "mail_client_service_api_client"
        if generated_client_dir.exists():
            print(f"Generated client package: {generated_client_dir}")
            print("Files:")
            for file_path in generated_client_dir.rglob("*.py"):
                print(f"  {file_path.relative_to(generated_client_dir)}")
        
    except FileNotFoundError:
        print("Error: openapi-python-client not found. Install with:")
        print("  pip install openapi-python-client")
        sys.exit(1)


if __name__ == "__main__":
    regenerate_client()
