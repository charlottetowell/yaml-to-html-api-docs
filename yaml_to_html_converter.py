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
        """
        Extract and organize API tags from both global definitions and endpoints.
        Also creates an "Uncategorized" tag if there are endpoints without tags.
        """
        # Get globally defined tags
        global_tags = {tag['name']: tag.get('description', '') for tag in self.spec_data.get('tags', [])}
        
        # Gather tags from endpoints
        endpoint_tags = set()
        has_untagged = False
        
        for path, methods in self.spec_data.get('paths', {}).items():
            for method, details in methods.items():
                tags = details.get('tags', [])
                if not tags:
                    has_untagged = True
                endpoint_tags.update(tags)
        
        # Combine global and endpoint tags
        all_tags = []
        
        # Add tags that are globally defined
        for tag_name, description in global_tags.items():
            all_tags.append({
                'name': tag_name,
                'description': description
            })
        
        # Add tags that are only defined in endpoints
        for tag_name in endpoint_tags:
            if tag_name not in global_tags:
                all_tags.append({
                    'name': tag_name,
                    'description': ''  # No description available for endpoint-only tags
                })
        
        # Add Uncategorized tag if needed
        if has_untagged:
            all_tags.append({
                'name': 'Uncategorized',
                'description': 'Operations without specific categorization'
            })
        
        return all_tags

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

    def read_svg_icon(self, icon_name: str) -> str:
        """Read SVG file content from the icons directory"""
        try:
            icon_path = os.path.join('icons', f'{icon_name}.svg')
            with open(icon_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except (FileNotFoundError, IOError):
            print(f"Warning: Icon {icon_name}.svg not found in /icons directory", file=sys.stderr)
            return ''

    def generate_sidebar_html(self, tags: list, api_info: Dict[str, Any], tag_endpoints: Dict[str, list]) -> str:
        """Generate HTML for the sidebar with tags that have endpoints"""
        # Only include tags that have endpoints
        active_tags = [tag for tag in tags if tag['name'] in tag_endpoints]
        
        # Get tag icon SVG
        tag_icon = self.read_svg_icon('tag')
        
        tags_html = '\n'.join([
            f'''            <li class="tag-item" data-tag="{tag["name"]}">
                <span class="tag-icon">{tag_icon}</span>
                <span class="tag-name">{tag["name"]}</span>
            </li>'''
            for tag in active_tags
        ])
        
        return f"""
        <div class="sidebar">
{self.generate_sidebar_header(api_info)}
            <ul class="tags-list">
{tags_html}
            </ul>
        </div>"""

    def organize_endpoints_by_tag(self) -> Dict[str, list]:
        """Organize endpoints by their tags, including handling of untagged endpoints"""
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
                
                # Get tags for this endpoint
                endpoint_tags = details['tags']
                
                if endpoint_tags:
                    # Add to each tag this endpoint belongs to
                    for tag in endpoint_tags:
                        if tag in tag_endpoints:
                            tag_endpoints[tag].append(endpoint_info)
                else:
                    # Add to Uncategorized if no tags
                    tag_endpoints['Uncategorized'].append(endpoint_info)
        
        # Remove empty tags
        return {tag: endpoints for tag, endpoints in tag_endpoints.items() if endpoints}

    def format_parameter_table(self, parameters: list) -> str:
        """Format parameters into an HTML table"""
        if not parameters:
            return '<p>No parameters required.</p>'
            
        # Separate parameters by location
        params_by_location = {
            'path': [],
            'query': [],
            'header': [],
            'body': []
        }
        
        for param in parameters:
            location = param.get('in', 'body')
            params_by_location[location].append(param)
            
        sections = []
        
        # Handle path, query, and header parameters
        simple_params = []
        for location in ['path', 'query', 'header']:
            simple_params.extend(params_by_location[location])
            
        if simple_params:
            rows = []
            for param in simple_params:
                required = '<span class="parameter-required">*</span>' if param.get('required', False) else ''
                description = param.get('description', '')
                param_type = param.get('type', 'string')
                
                rows.append(f'''                <tr>
                    <td>{param['name']}{required}</td>
                    <td>{param.get('in', 'body')}</td>
                    <td>{param_type}</td>
                    <td>{description}</td>
                </tr>''')
                
            sections.append(f'''            <div class="parameter-section">
                <h5 class="endpoint-section-subtitle">URL Parameters</h5>
                <table class="parameter-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Location</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
{''.join(rows)}
                    </tbody>
                </table>
            </div>''')
            
        # Handle body parameters
        body_params = params_by_location['body']
        if body_params:
            for param in body_params:
                if 'schema' in param:
                    schema_json = self.format_schema_as_json(param['schema'])
                    example = param.get('example') or param.get('schema', {}).get('example')
                    
                    sections.append(f'''            <div class="parameter-section">
                <h5 class="endpoint-section-subtitle">Request Body Schema</h5>
                <pre class="code-block">{schema_json}</pre>''')
                    
                    if example:
                        import json
                        try:
                            formatted_example = json.dumps(example, indent=2)
                        except (TypeError, ValueError):
                            formatted_example = str(example)
                            
                        sections.append(f'''                <h5 class="endpoint-section-subtitle">Request Body Example</h5>
                <pre class="code-block">{formatted_example}</pre>''')
                        
                    sections.append('            </div>')
                else:
                    # Handle non-schema body parameters
                    sections.append(f'''            <div class="parameter-section">
                <h5 class="endpoint-section-subtitle">Request Body</h5>
                <p>{param.get('description', 'No description available.')}</p>
                <table class="parameter-table">
                    <tr>
                        <th>Content Type</th>
                        <td>{param.get('consumes', ['application/json'])[0]}</td>
                    </tr>
                    <tr>
                        <th>Required</th>
                        <td>{"Yes" if param.get('required', False) else "No"}</td>
                    </tr>
                </table>
            </div>''')
                    
        return '\n'.join(sections) if sections else '<p>No parameters required.</p>'

    def format_request_content_type(self, operation: Dict[str, Any]) -> str:
        """Format request content type information"""
        consumes = operation.get('consumes', ['application/json'])
        if len(consumes) == 1:
            return consumes[0]
        return ', '.join(consumes)

    def format_schema_as_json(self, schema: Dict[str, Any], indent_level: int = 0) -> str:
        """Convert OpenAPI/Swagger schema to JSON-like structure with types"""
        if not schema:
            return "{}"
            
        def _indent(level: int) -> str:
            return "  " * level

        result = []
        
        if 'type' in schema:
            if schema['type'] == 'object' and 'properties' in schema:
                result.append("{")
                properties = schema['properties']
                required = schema.get('required', [])
                
                for i, (prop_name, prop_schema) in enumerate(properties.items()):
                    is_required = prop_name in required
                    prop_type = prop_schema.get('type', 'any')
                    description = prop_schema.get('description', '')
                    
                    # Handle nested objects
                    if prop_type == 'object' and 'properties' in prop_schema:
                        nested_value = self.format_schema_as_json(prop_schema, indent_level + 1)
                        line = f'{_indent(indent_level + 1)}"{prop_name}": {nested_value}'
                    # Handle arrays
                    elif prop_type == 'array' and 'items' in prop_schema:
                        items_schema = prop_schema['items']
                        if 'type' in items_schema:
                            if items_schema['type'] == 'object':
                                nested_value = self.format_schema_as_json(items_schema, indent_level + 2)
                                line = f'{_indent(indent_level + 1)}"{prop_name}": [\n{_indent(indent_level + 2)}{nested_value}\n{_indent(indent_level + 1)}]'
                            else:
                                line = f'{_indent(indent_level + 1)}"{prop_name}": [ ({items_schema["type"]}) ]'
                        else:
                            line = f'{_indent(indent_level + 1)}"{prop_name}": [ (any) ]'
                    # Handle primitive types
                    else:
                        type_info = f"({prop_type})"
                        if description:
                            type_info += f" // {description}"
                        if is_required:
                            type_info += " *"
                        line = f'{_indent(indent_level + 1)}"{prop_name}": {type_info}'
                    
                    if i < len(properties) - 1:
                        line += ","
                    result.append(line)
                
                result.append(f"{_indent(indent_level)}}}")
            elif schema['type'] == 'array' and 'items' in schema:
                items_schema = schema['items']
                if 'type' in items_schema:
                    if items_schema['type'] == 'object':
                        nested_value = self.format_schema_as_json(items_schema, indent_level)
                        result.append(f"[\n{_indent(indent_level + 1)}{nested_value}\n{_indent(indent_level)}]")
                    else:
                        result.append(f"[ ({items_schema['type']}) ]")
                else:
                    result.append("[ (any) ]")
            else:
                result.append(f"({schema['type']})")
        else:
            result.append("(any)")
            
        return '\n'.join(result)

    def format_response_example(self, responses: Dict[str, Any]) -> str:
        """Format response examples and schemas into HTML"""
        examples = []
        for status_code, response in responses.items():
            schema = response.get('schema', {})
            example = response.get('example') or schema.get('example')
            description = response.get('description', '')
            
            # Start the response section
            examples.append(f'''            <div class="endpoint-section">
                <h4 class="endpoint-section-title">Response {status_code}</h4>
                <p>{description}</p>''')
            
            # If there's a schema, show it first
            if schema:
                schema_json = self.format_schema_as_json(schema)
                examples.append(f'''                <div class="response-schema">
                    <h5 class="endpoint-section-subtitle">Schema</h5>
                    <pre class="code-block">{schema_json}</pre>
                </div>''')
            
            # If there's an example, show it after the schema
            if example:
                import json
                try:
                    formatted_example = json.dumps(example, indent=2)
                except (TypeError, ValueError):
                    formatted_example = str(example)
                
                examples.append(f'''                <div class="response-example">
                    <h5 class="endpoint-section-subtitle">Example</h5>
                    <pre class="code-block">{formatted_example}</pre>
                </div>''')
            
            examples.append('            </div>')
                
        return '\n'.join(examples)

    def format_security_info(self, security: list, definitions: Dict[str, Any]) -> str:
        """Format security information into HTML"""
        if not security:
            return ''
            
        security_html = []
        for sec_req in security:
            for sec_name, scopes in sec_req.items():
                if sec_name in definitions:
                    sec_def = definitions[sec_name]
                    security_html.append(f'''            <div class="security-info">
                <span class="endpoint-security-icon">{self.read_svg_icon('lock')}</span>
                <div>
                    <strong>{sec_def.get('type', '').title()} Authentication</strong>
                    <p>{sec_def.get('description', '')}</p>
                </div>
            </div>''')
                    
        return '\n'.join(security_html)

    def generate_endpoint_sections(self, tag_endpoints: Dict[str, list]) -> str:
        """Generate HTML for all endpoint sections"""
        sections = []
        tags_info = {tag['name']: tag.get('description', '') for tag in self.extract_tags()}
        security_definitions = self.extract_security_definitions()
        
        for tag, endpoints in tag_endpoints.items():
            tag_description = tags_info.get(tag, '')
            description_html = f'\n            <p class="tag-description">{tag_description}</p>' if tag_description else ''
            
            endpoints_html = []
            for endpoint in endpoints:
                path = endpoint['path']
                method = endpoint['method']
                details = self.spec_data['paths'][path][method.lower()]
                
                # Check if endpoint has security
                has_security = bool(details.get('security', []))
                security_icon = f'<span class="endpoint-security-icon">{self.read_svg_icon("lock")}</span>' if has_security else ''
                
                # Get content type
                content_type = self.format_request_content_type(details)
                content_type_html = f'<span class="endpoint-content-type">{content_type}</span>' if content_type != 'application/json' else ''
                
                # Generate detailed view
                parameters_html = self.format_parameter_table(details.get('parameters', []))
                responses_html = self.format_response_example(details.get('responses', {}))
                security_html = self.format_security_info(details.get('security', []), security_definitions)
                
                endpoints_html.append(f'''            <div class="endpoint-preview" data-path="{path}" data-method="{method}">
                <div class="endpoint-preview-header">
                    <span class="endpoint-method method method-{method.lower()}">{method}</span>
                    <span class="endpoint-path">{path}</span>
                    <span class="endpoint-description">{details.get('summary', '')}</span>
                    {security_icon}
                    {content_type_html}
                </div>
                <div class="endpoint-details">
                    <div class="endpoint-full-description">{details.get('description', '')}</div>
                    <div class="endpoint-section">
                        <h3 class="endpoint-section-title">Parameters</h3>
                        {parameters_html}
                    </div>
                    <div class="endpoint-section">
                        <h3 class="endpoint-section-title">Responses</h3>
                        {responses_html}
                    </div>
                    {security_html}
                </div>
            </div>''')
            
            sections.append(f'''
        <section id="tag-section-{tag}" class="tag-section">
            <div class="tag-section-marker" data-tag="{tag}"></div>
            <h2 class="tag-section-title">{tag}</h2>{description_html}
{''.join(endpoints_html)}
        </section>''')
        
        return '\n'.join(sections)

    def generate_intersection_observer_js(self) -> str:
        """Generate JavaScript for intersection observer and smooth scrolling"""
        return """
    <script>
        // Track current active section
        let currentActiveTag = null;

        // Intersection Observer for tag highlighting
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const tag = entry.target.dataset.tag;
                const tagItem = document.querySelector(`.tag-item[data-tag="${tag}"]`);
                
                if (entry.isIntersecting) {
                    // Update current active tag
                    currentActiveTag = tag;
                    
                    // Remove active class from all tags
                    document.querySelectorAll('.tag-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    
                    // Add active class to current tag
                    if (tagItem) {
                        tagItem.classList.add('active');
                        // Ensure the active tag is visible in the sidebar
                        tagItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }
            });
        }, {
            rootMargin: '-20% 0px -79% 0px',
            threshold: [0, 0.25, 0.5, 0.75, 1]
        });

        // Observe all section markers
        document.querySelectorAll('.tag-section-marker').forEach(marker => {
            observer.observe(marker);
        });

        // Click handlers for tag items
        document.querySelectorAll('.tag-item').forEach(item => {
            item.addEventListener('click', () => {
                const tag = item.dataset.tag;
                const section = document.getElementById(`tag-section-${tag}`);
                if (section) {
                    // Remove active class from all tags
                    document.querySelectorAll('.tag-item').forEach(tagItem => {
                        tagItem.classList.remove('active');
                    });
                    
                    // Add active class to clicked tag
                    item.classList.add('active');
                    
                    // Scroll to section
                    section.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Add scroll event listener for more precise tracking
        document.querySelector('.main-content').addEventListener('scroll', () => {
            // Find all tag sections
            const sections = document.querySelectorAll('.tag-section');
            const mainContent = document.querySelector('.main-content');
            
            // Get the current scroll position
            const scrollPosition = mainContent.scrollTop + mainContent.offsetHeight * 0.2;
            
            // Find the current section
            let currentSection = null;
            sections.forEach(section => {
                if (section.offsetTop <= scrollPosition) {
                    currentSection = section;
                }
            });
            
            if (currentSection) {
                const tag = currentSection.querySelector('.tag-section-marker').dataset.tag;
                if (tag !== currentActiveTag) {
                    // Update active tag
                    document.querySelectorAll('.tag-item').forEach(item => {
                        item.classList.remove('active');
                        if (item.dataset.tag === tag) {
                            item.classList.add('active');
                            currentActiveTag = tag;
                        }
                    });
                }
            }
        });
    </script>"""

    def format_base_url(self) -> str:
        """Format the complete base URL with scheme"""
        host = self.spec_data.get('host', '')
        base_path = self.spec_data.get('basePath', '')
        schemes = self.spec_data.get('schemes', ['https'])
        
        # Use the first scheme (usually https or http)
        scheme = schemes[0] if schemes else 'https'
        
        # Combine all parts, ensuring no double slashes
        base_url = f"{scheme}://{host}"
        if base_path:
            # Ensure base_path starts with / and doesn't end with /
            base_path = f"/{base_path.strip('/')}"
            base_url = f"{base_url}{base_path}"
            
        return base_url

    def generate_copy_script(self) -> str:
        """Generate JavaScript for copy functionality"""
        return """
    <script>
        function setupCopyButtons() {
            document.querySelectorAll('.copy-button').forEach(button => {
                button.addEventListener('click', async () => {
                    const textToCopy = button.getAttribute('data-copy');
                    const copyIcon = button.querySelector('.copy-icon');
                    const tickIcon = button.querySelector('.tick-icon');
                    
                    try {
                        await navigator.clipboard.writeText(textToCopy);
                        
                        // Show tick icon
                        copyIcon.style.display = 'none';
                        tickIcon.style.display = 'block';
                        button.classList.add('copied');
                        
                        // Reset after 2 seconds
                        setTimeout(() => {
                            copyIcon.style.display = 'block';
                            tickIcon.style.display = 'none';
                            button.classList.remove('copied');
                        }, 2000);
                    } catch (err) {
                        console.error('Failed to copy text:', err);
                    }
                });
            });
        }
        
        // Initialize copy buttons when the page loads
        document.addEventListener('DOMContentLoaded', setupCopyButtons);
    </script>
    """

    def generate_endpoint_script(self) -> str:
        """Generate JavaScript for endpoint expansion/collapse"""
        return """
    <script>
        // Handle endpoint expansion/collapse
        document.querySelectorAll('.endpoint-preview').forEach(endpoint => {
            endpoint.addEventListener('click', (e) => {
                // Don't toggle if clicking inside a code block or table
                if (e.target.closest('.code-block') || e.target.closest('.parameter-table')) {
                    return;
                }
                
                // Close any other open endpoints
                document.querySelectorAll('.endpoint-preview.expanded').forEach(openEndpoint => {
                    if (openEndpoint !== endpoint) {
                        openEndpoint.classList.remove('expanded');
                    }
                });
                
                // Toggle current endpoint
                endpoint.classList.toggle('expanded');
            });
        });
    </script>"""

    def generate_html(self, output_path: str) -> None:
        """Generate HTML documentation from the parsed API spec"""
        api_info = self.extract_api_info()
        tags = self.extract_tags()
        tag_endpoints = self.organize_endpoints_by_tag()
        base_url = self.format_base_url()

        # Get icons
        copy_icon = self.read_svg_icon('copy')
        tick_icon = self.read_svg_icon('tick')

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
{self.generate_sidebar_html(tags, api_info, tag_endpoints)}
        <main class="main-content">
            <div class="api-header">
                <h1 class="api-title">{api_info['title']}</h1>
                <p class="api-description">{api_info['description']}</p>
                <div class="api-base-url">
                    <span class="api-base-url-label">Base URL</span>
                    <code class="api-base-url-value">{base_url}</code>
                    <button class="copy-button" data-copy="{base_url}" title="Copy base URL">
                        <span class="copy-icon" style="display: block">{copy_icon}</span>
                        <span class="tick-icon" style="display: none">{tick_icon}</span>
                    </button>
                </div>
            </div>
{self.generate_endpoint_sections(tag_endpoints)}
        </main>
    </div>
{self.generate_intersection_observer_js()}
{self.generate_copy_script()}
{self.generate_endpoint_script()}
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