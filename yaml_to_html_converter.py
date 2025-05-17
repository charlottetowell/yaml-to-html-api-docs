#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import yaml
import os
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
    
    def check_for_logo(self) -> bool:
        """Check if logo.png exists in the current directory"""
        return os.path.isfile('logo.png')

    def generate_sidebar_header(self, api_info: Dict[str, Any]) -> str:
        """Generate the sidebar header with optional logo"""
        has_logo = self.check_for_logo()
        
        logo_html = """
                <div class="sidebar-logo">
                    <img src="logo.png" alt="API Documentation Logo">
                </div>""" if has_logo else ""
        
        return f"""
            <div class="sidebar-header">
                {logo_html}
                <h1 class="sidebar-title">API Documentation</h1>
                <div class="api-version">Version {api_info['version']}</div>
            </div>"""

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

    def generate_sidebar_html(self, tags: list, api_info: Dict[str, Any]) -> str:
        """Generate HTML for the sidebar with tags"""
        tags_html = '\n'.join([
            f'            <li class="tag-item" data-tag="{tag["name"]}">{tag["name"]}</li>'
            for tag in tags
        ])
        
        return f"""
        <div class="sidebar">
{self.generate_sidebar_header(api_info)}
            <ul class="tags-list">
{tags_html}
            </ul>
        </div>"""

    def organize_endpoints_by_tag(self) -> Dict[str, list]:
        """Organize endpoints by their tags"""
        tag_endpoints = {}
        endpoints = self.extract_endpoints()
        
        # Initialize tags with empty lists
        for tag in self.extract_tags():
            tag_endpoints[tag['name']] = []
        
        # Group endpoints by tag
        for path, methods in endpoints.items():
            for method, details in methods.items():
                endpoint_info = {
                    'path': path,
                    'method': method.upper(),
                    'summary': details['summary'],
                    'description': details['description']
                }
                
                # Add to each tag this endpoint belongs to
                for tag in details['tags']:
                    if tag in tag_endpoints:
                        tag_endpoints[tag].append(endpoint_info)
        
        return tag_endpoints

    def generate_endpoint_sections(self, tag_endpoints: Dict[str, list]) -> str:
        """Generate HTML for all endpoint sections"""
        sections = []
        
        for tag, endpoints in tag_endpoints.items():
            endpoints_html = '\n'.join([
                f'''            <div class="endpoint-preview">
                <span class="endpoint-method method method-{endpoint['method'].lower()}">{endpoint['method']}</span>
                <span class="endpoint-path">{endpoint['path']}</span>
                <span class="endpoint-description">{endpoint['description'] or endpoint['summary']}</span>
            </div>''' for endpoint in endpoints
            ])
            
            sections.append(f'''
        <section id="tag-{tag.lower()}" class="tag-section">
            <div class="tag-section-marker" data-tag="{tag}"></div>
            <h2 class="tag-section-title">{tag}</h2>
{endpoints_html}
        </section>''')
        
        return '\n'.join(sections)

    def generate_intersection_observer_js(self) -> str:
        """Generate JavaScript for intersection observer and smooth scrolling"""
        return """
    <script>
        // Intersection Observer for tag highlighting
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const tag = entry.target.dataset.tag;
                    document.querySelectorAll('.tag-item').forEach(item => {
                        item.classList.remove('active');
                        if (item.dataset.tag === tag) {
                            item.classList.add('active');
                        }
                    });
                }
            });
        }, {
            threshold: 1.0,
            rootMargin: '-100px 0px -90% 0px'
        });

        // Observe all section markers
        document.querySelectorAll('.tag-section-marker').forEach(marker => {
            observer.observe(marker);
        });

        // Click handlers for tag items
        document.querySelectorAll('.tag-item').forEach(item => {
            item.addEventListener('click', () => {
                const tag = item.dataset.tag;
                const section = document.getElementById(`tag-${tag.toLowerCase()}`);
                if (section) {
                    section.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    </script>"""

    def generate_html(self, output_path: str) -> None:
        """Generate HTML documentation from the parsed API spec"""
        api_info = self.extract_api_info()
        tags = self.extract_tags()
        tag_endpoints = self.organize_endpoints_by_tag()

        # Generate HTML structure
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{api_info['title']}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
{self.generate_sidebar_html(tags, api_info)}
        <main class="main-content">
            <div class="api-header">
                <h1 class="api-title">{api_info['title']}</h1>
                <p class="api-description">{api_info['description']}</p>
                <div class="api-base-url">{api_info['base_url']}</div>
            </div>
{self.generate_endpoint_sections(tag_endpoints)}
        </main>
    </div>
{self.generate_intersection_observer_js()}
</body>
</html>"""

        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
            print(f"\n✨ Documentation generated successfully!")
            print(f"📄 Output file: {output_path}")
            print(f"🎨 Style file: styles.css")
            print("\nYou can now:")
            print("1. Open the HTML file in your browser")
            print("2. Customize the appearance by modifying styles.css")
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