#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ConverterConfig:
    """Configuration class for future styling and formatting options"""
    # Template for future configuration options
    template_path: Optional[str] = None
    output_style: str = "default"
    # Add more configuration options here as needed

class APISpecConverter:
    def __init__(self, config: Optional[ConverterConfig] = None):
        self.config = config or ConverterConfig()
        self.spec_data: Dict[str, Any] = {}
    
    def load_spec(self, yaml_path: str) -> None:
        """Load and parse the YAML API specification"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                self.spec_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print(f"File not found: {yaml_path}", file=sys.stderr)
            sys.exit(1)

    def extract_api_info(self) -> Dict[str, Any]:
        """Extract basic API information"""
        return {
            'title': self.spec_data.get('info', {}).get('title', ''),
            'description': self.spec_data.get('info', {}).get('description', ''),
            'version': self.spec_data.get('info', {}).get('version', ''),
            'base_url': f"{self.spec_data.get('host', '')}{self.spec_data.get('basePath', '')}"
        }

    def extract_tags(self) -> list:
        """Extract and organize API tags"""
        return self.spec_data.get('tags', [])

    def extract_endpoints(self) -> Dict[str, Any]:
        """Extract and organize API endpoints"""
        endpoints = {}
        paths = self.spec_data.get('paths', {})
        
        for path, methods in paths.items():
            endpoints[path] = {}
            for method, details in methods.items():
                endpoints[path][method] = {
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'tags': details.get('tags', []),
                    'parameters': details.get('parameters', []),
                    'responses': details.get('responses', {}),
                    'security': details.get('security', [])
                }
        
        return endpoints

    def extract_security_definitions(self) -> Dict[str, Any]:
        """Extract security definitions"""
        return self.spec_data.get('securityDefinitions', {})

    def generate_html(self, output_path: str) -> None:
        """Generate HTML documentation from the parsed API spec"""
        # This is a placeholder for the HTML generation logic
        # Will be implemented based on future styling and formatting requirements
        api_info = self.extract_api_info()
        tags = self.extract_tags()
        endpoints = self.extract_endpoints()
        security = self.extract_security_definitions()

        # Temporary basic HTML output for testing
        basic_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{api_info['title']}</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>{api_info['title']}</h1>
            <p>{api_info['description']}</p>
            <p>Version: {api_info['version']}</p>
        </body>
        </html>
        """

        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(basic_html)
        except IOError as e:
            print(f"Error writing HTML file: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert OpenAPI/Swagger YAML to HTML documentation')
    parser.add_argument('input_file', help='Path to the input YAML file')
    parser.add_argument('output_file', help='Path for the output HTML file')
    # Template for future command line arguments
    parser.add_argument('--template', help='Path to custom HTML template', default=None)
    parser.add_argument('--style', help='Output style configuration', default='default')
    
    args = parser.parse_args()

    # Create configuration object
    config = ConverterConfig(
        template_path=args.template,
        output_style=args.style
    )

    # Initialize and run converter
    converter = APISpecConverter(config)
    converter.load_spec(args.input_file)
    converter.generate_html(args.output_file)

if __name__ == "__main__":
    main() 