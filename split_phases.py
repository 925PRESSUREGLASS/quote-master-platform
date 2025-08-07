#!/usr/bin/env python3
"""
Quote Master Pro - Phase Splitter Script
Breaks the master prompt into VS Code-compatible chunks for Continue.dev/Copilot
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class PhasePromptSplitter:
    def __init__(self, master_prompt_file: str = "COMPLETE_IMPLEMENTATION_PLAN.md"):
        self.master_prompt_file = master_prompt_file
        self.output_dir = Path(".prompts")
        self.phases = {}
        
    def split_master_prompt(self) -> Dict[str, str]:
        """Split the master prompt into manageable phases"""
        
        if not os.path.exists(self.master_prompt_file):
            print(f"❌ Master prompt file not found: {self.master_prompt_file}")
            return {}
            
        with open(self.master_prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by phase headers
        phase_pattern = r'## \*\*PHASE \d+:([^*]+)\*\*'
        phases = re.split(phase_pattern, content)
        
        phase_dict = {}
        for i in range(1, len(phases), 2):
            if i + 1 < len(phases):
                phase_name = phases[i].strip()
                phase_content = phases[i + 1]
                
                # Clean up the content
                phase_content = self._clean_phase_content(phase_content, phase_name)
                phase_dict[f"phase{(i+1)//2}_{phase_name.lower().replace(' ', '_').replace('&', 'and')}"] = phase_content
        
        return phase_dict
    
    def _clean_phase_content(self, content: str, phase_name: str) -> str:
        """Clean and format phase content for VS Code tools"""
        
        # Create a focused prompt for this phase
        prompt = f"""# 🚀 Quote Master Pro - {phase_name}

## Context
You are implementing Quote Master Pro, an enterprise-grade AI-powered quote generation platform. This is {phase_name} of a 9-phase implementation plan.

## Current Project Structure
- **Backend**: FastAPI with SQLAlchemy, multi-provider AI service (OpenAI/Claude/Azure)
- **Frontend**: React with TypeScript, Tailwind CSS
- **Database**: PostgreSQL with Redis caching
- **Architecture**: Clean architecture with domain-driven design

## Phase Objective
{content}

## Implementation Instructions
1. Generate complete, production-ready implementations
2. Include comprehensive error handling and logging
3. Add type hints for Python code and proper TypeScript types
4. Follow existing code patterns and architecture
5. Include docstrings and comments for complex logic
6. Consider performance, security, and scalability
7. Generate corresponding test files where applicable

## Quality Requirements
- ✅ Production-ready code with error handling
- ✅ Comprehensive logging and monitoring
- ✅ Type safety (Python type hints, TypeScript)
- ✅ Security best practices
- ✅ Performance optimization
- ✅ Documentation and comments

## File Generation Format
When generating files, use this format:
```
# File: path/to/file.py
# Dependencies: package1>=1.0.0, package2>=2.0.0
# Description: Brief description of the file purpose

[Complete file content here]
```

Generate all files needed for this phase. Ask if you need clarification on any requirements.
"""
        return prompt
    
    def create_phase_files(self):
        """Create individual phase files for VS Code"""
        
        self.output_dir.mkdir(exist_ok=True)
        
        phases = self.split_master_prompt()
        
        if not phases:
            print("❌ No phases found to split")
            return
        
        # Create instructions file
        self._create_instructions_file()
        
        # Create individual phase files
        for phase_key, content in phases.items():
            filename = f"{phase_key}.md"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Created: {filename}")
        
        print(f"\n🎯 Generated {len(phases)} phase files in .prompts/")
        print(f"📊 Total prompts ready for VS Code Continue.dev/Copilot")
        
        return phases
    
    def _create_instructions_file(self):
        """Create instructions for using the phase files"""
        
        instructions = """# 🎯 Quote Master Pro - VS Code Implementation Guide

## 📋 Phase Files Overview

This directory contains split prompts optimized for VS Code Continue.dev or GitHub Copilot:

### 📁 Available Phase Files:
1. **phase1_enhanced_ai_service_infrastructure.md** (3-4 days)
   - OpenTelemetry integration, smart routing, circuit breakers
   
2. **phase2_comprehensive_testing_infrastructure.md** (4-5 days)  
   - 95% test coverage, security tests, performance tests
   
3. **phase3_production_security_and_middleware.md** (3-4 days)
   - Enterprise security, JWT auth, rate limiting
   
4. **phase4_business_logic_and_domain_services.md** (5-6 days)
   - Quote generation, analytics, notifications, billing
   
5. **phase5_data_access_and_repository_layer.md** (3-4 days)
   - Repository pattern, caching, database optimization
   
6. **phase6_frontend_optimization_and_features.md** (4-5 days)
   - Performance optimization, UI components, PWA
   
7. **phase7_devops_and_deployment_infrastructure.md** (4-5 days)
   - Docker, Kubernetes, CI/CD, Infrastructure as Code
   
8. **phase8_monitoring_and_observability_stack.md** (3-4 days)
   - Prometheus, Grafana, logging, alerting
   
9. **phase9_documentation_and_api_specifications.md** (2-3 days)
   - OpenAPI docs, developer guides, runbooks

## 🚀 How to Use in VS Code

### Option 1: Continue.dev Extension (Recommended)
```bash
1. Install Continue.dev extension in VS Code
2. Configure with OpenAI API key in ~/.continue/config.json
3. Open Continue sidebar (Ctrl+Shift+M or Cmd+Shift+M)
4. Copy content from phase file
5. Paste into Continue chat
6. Generate code files one by one
7. Review and save to appropriate locations
```

### Option 2: GitHub Copilot Chat
```bash
1. Ensure GitHub Copilot subscription is active
2. Open Copilot Chat (Ctrl+Shift+I or Cmd+Shift+I)
3. Copy content from phase file
4. Paste and request code generation
5. Review generated code before accepting
```

## 📋 Implementation Workflow

### Phase Execution Steps:
1. **Open Phase File**: Open the current phase .md file
2. **Copy Content**: Copy the entire prompt content  
3. **Paste to AI Tool**: Use Continue.dev or Copilot Chat
4. **Generate Code**: Request file generation one by one
5. **Review & Test**: Review generated code and run tests
6. **Commit Changes**: Git commit completed phase
7. **Move to Next**: Proceed to next phase

### Quality Checkpoints:
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Code follows project patterns
- [ ] Security considerations addressed
- [ ] Performance optimized
- [ ] Documentation included

## 🎯 Pro Tips

### For Better Results:
- **Generate one file at a time** for complex components
- **Ask for specific file types**: "Generate the FastAPI router file"  
- **Request tests separately**: "Generate comprehensive tests for this service"
- **Specify file paths**: "Save to src/services/ai/monitoring/tracing.py"

### If Generation Stops:
- **Continue prompt**: "Continue generating the rest of the file"
- **Ask for specific sections**: "Generate the remaining methods"
- **Break into smaller parts**: Request specific functions/classes

### Token Management:
- Each phase file is ~2,000-3,000 tokens (safe for VS Code tools)
- If still too long, focus on one task section at a time
- Use "Generate X only" to focus on specific components

## 🚨 Important Notes

### Before Starting:
- [ ] Backup your current project
- [ ] Create a new branch: `git checkout -b implementation-phase-X`
- [ ] Ensure dependencies are installed
- [ ] Test current functionality works

### During Implementation:
- [ ] Test frequently as you generate code
- [ ] Follow existing code patterns and styles
- [ ] Update requirements.txt/package.json as needed
- [ ] Document any architectural decisions

### After Each Phase:
- [ ] Run full test suite
- [ ] Check for integration issues  
- [ ] Update documentation
- [ ] Commit with descriptive message
- [ ] Tag phase completion

## 🎖️ Success Metrics per Phase

### Phase 1: Enhanced AI Service
- [ ] OpenTelemetry tracing working
- [ ] Smart routing implemented
- [ ] Circuit breakers functional
- [ ] Health monitoring dashboard

### Phase 2: Testing Infrastructure  
- [ ] 95%+ test coverage achieved
- [ ] All test types implemented
- [ ] CI/CD integration working
- [ ] Quality gates enforced

... (continue for each phase)

## 🆘 Troubleshooting

### Common Issues:
- **"Code too long"**: Ask for specific sections
- **"Context lost"**: Restart and provide file context  
- **"Import errors"**: Check dependencies and file paths
- **"Tests failing"**: Generate tests separately and debug

### Getting Help:
- Reference the full `COMPLETE_IMPLEMENTATION_PLAN.md`
- Check existing code patterns in the project
- Use VS Code's built-in error highlighting
- Test incrementally as you build

---

**🎯 Ready to build Quote Master Pro! Start with Phase 1 when ready.**
"""
        
        instructions_file = self.output_dir / "README.md"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print(f"✅ Created: README.md (usage instructions)")
    
    def create_vscode_tasks(self):
        """Create VS Code task runner for easy access to phases"""
        
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)
        
        tasks = {
            "version": "2.0.0",
            "tasks": []
        }
        
        phases = [
            ("Phase 1: AI Service", "phase1_enhanced_ai_service_infrastructure.md"),
            ("Phase 2: Testing", "phase2_comprehensive_testing_infrastructure.md"),
            ("Phase 3: Security", "phase3_production_security_and_middleware.md"),
            ("Phase 4: Business Logic", "phase4_business_logic_and_domain_services.md"),
            ("Phase 5: Data Layer", "phase5_data_access_and_repository_layer.md"),
            ("Phase 6: Frontend", "phase6_frontend_optimization_and_features.md"),
            ("Phase 7: DevOps", "phase7_devops_and_deployment_infrastructure.md"),
            ("Phase 8: Monitoring", "phase8_monitoring_and_observability_stack.md"),
            ("Phase 9: Documentation", "phase9_documentation_and_api_specifications.md")
        ]
        
        for i, (name, filename) in enumerate(phases, 1):
            task = {
                "label": f"Open {name}",
                "type": "shell",
                "command": "code",
                "args": [f".prompts/{filename}"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "silent",
                    "focus": False,
                    "panel": "shared"
                },
                "problemMatcher": []
            }
            tasks["tasks"].append(task)
        
        # Add a task to open all phases
        tasks["tasks"].append({
            "label": "Open All Phases",
            "type": "shell", 
            "command": "code",
            "args": [".prompts/"],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "silent", 
                "focus": False,
                "panel": "shared"
            },
            "problemMatcher": []
        })
        
        tasks_file = vscode_dir / "tasks.json"
        import json
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
        
        print(f"✅ Created: .vscode/tasks.json (VS Code task runner)")

def main():
    """Main execution function"""
    print("🚀 Quote Master Pro - Phase Splitter")
    print("=" * 50)
    
    splitter = PhasePromptSplitter()
    
    # Create phase files
    phases = splitter.create_phase_files()
    
    if not phases:
        return
    
    # Create VS Code tasks
    splitter.create_vscode_tasks()
    
    print("\n" + "=" * 50)
    print("🎯 Setup Complete!")
    print("\nNext Steps:")
    print("1. Install Continue.dev extension in VS Code")
    print("2. Configure with your OpenAI API key") 
    print("3. Open .prompts/README.md for detailed instructions")
    print("4. Start with Phase 1: Enhanced AI Service")
    print("5. Use Ctrl+Shift+P → 'Tasks: Run Task' → 'Open Phase 1: AI Service'")
    print("\n📁 All phase files ready in .prompts/ directory")
    print("🔧 VS Code tasks configured for easy access")
    print("\n🚀 Ready to build Quote Master Pro!")

if __name__ == "__main__":
    main()
