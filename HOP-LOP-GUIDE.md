# HOP/LOP Multi-Agent Orchestration Guide

A practical guide for using HOP (Higher Order Prompt) to orchestrate multiple LOP (Lower Order Prompt) agents in parallel using nano-agent with Claude Code or Cursor.

## 🚀 Quick Start

### What is HOP/LOP?

- **HOP (Higher Order Prompt)**: The orchestrator that coordinates multiple agents
- **LOP (Lower Order Prompt)**: Individual focused tasks executed by specific agents
- **Benefit**: Execute multiple tasks in parallel, reducing time from sequential hours to parallel minutes

## 📋 Available Commands

### Core HOP Commands

1. **`/hop-orchestrator`** - Main orchestration command for complex multi-task workflows
2. **`/hop-parallel-execution`** - Execute specific parallel tasks quickly  
3. **`/hop-multi-task`** - Pre-configured workflows (analyze, develop, test, document, optimize)

### LOP Templates (in `.claude/commands/lops/`)

- `lop-analyze-structure.md` - Code structure analysis
- `lop-create-tests.md` - Test generation
- `lop-create-docs.md` - Documentation creation
- `lop-security-scan.md` - Security vulnerability scanning
- `lop-optimize-code.md` - Code optimization

## 💻 Usage Examples

### Example 1: Complete Code Review (4 agents in parallel)

```bash
/hop-multi-task analyze
```

This launches simultaneously:
- Structure analysis (gpt-5-mini)
- Security scan (claude-3-haiku)  
- Performance review (gpt-5-nano)
- Code quality check (gpt-oss-20b)

**Time saved**: ~75% (4 sequential tasks → 1 parallel execution)

### Example 2: Feature Implementation

```bash
/hop-orchestrator "Implement user authentication with JWT tokens"
```

Automatically launches:
- API endpoint creation (gpt-5)
- Frontend component (claude-sonnet-4)
- Test generation (gpt-5-mini)
- Documentation (claude-3-haiku)

### Example 3: Custom Parallel Tasks

In Claude Code, execute simultaneously:

```
@agent-nano-agent-gpt-5 "Create a REST API for user management"
@agent-nano-agent-claude-sonnet-4 "Generate React components for user CRUD"
@agent-nano-agent-gpt-5-mini "Write comprehensive tests"
@agent-nano-agent-claude-3-haiku "Create API documentation"
```

## 🎯 Agent Selection Strategy

### Speed-Optimized Agents
- **gpt-5-nano**: Fastest, simple tasks (formatting, basic checks)
- **claude-3-haiku**: Fast, efficient (quick scans, simple generation)
- **gpt-5-mini**: Balanced (standard development tasks)

### Quality-Optimized Agents
- **gpt-5**: Complex reasoning (architecture, optimization)
- **claude-opus-4-1**: Detailed analysis (comprehensive reviews)
- **claude-sonnet-4**: Balanced quality (documentation, testing)

### Cost-Optimized Agents (Local)
- **gpt-oss-20b**: Free, good for bulk operations
- **gpt-oss-120b**: Free, more capable for complex tasks

## 📊 Performance Comparison

| Workflow | Sequential Time | Parallel Time | Time Saved | Agents Used |
|----------|----------------|---------------|------------|-------------|
| Code Review | ~20 min | ~5 min | 75% | 4 agents |
| Feature Dev | ~30 min | ~8 min | 73% | 4 agents |
| Test Suite | ~15 min | ~5 min | 67% | 3 agents |
| Documentation | ~25 min | ~7 min | 72% | 4 agents |

## 🔧 Setting Up Your Workflow

### Step 1: Identify Parallel Tasks
Look for tasks that:
- Don't depend on each other
- Can be clearly scoped
- Would benefit from different model strengths

### Step 2: Choose Your Pattern

**Option A: Use Pre-built Commands**
```bash
/hop-multi-task [analyze|develop|test|document|optimize]
```

**Option B: Custom Orchestration**
```bash
/hop-orchestrator "your complex task description"
```

**Option C: Direct Parallel Execution**
```
@agent-nano-agent-[model] "specific task 1"
@agent-nano-agent-[model] "specific task 2"
@agent-nano-agent-[model] "specific task 3"
```

### Step 3: Execute and Aggregate
- All agents run simultaneously
- Results collected as they complete
- HOP aggregates findings into unified output

## 📝 Real-World Workflows

### Workflow: Morning Code Review
```bash
/hop-multi-task analyze src/
```
- Runs 4 analyses in parallel
- Complete review in 5 minutes
- Prioritized findings across security, performance, structure, and quality

### Workflow: Feature Sprint
```bash
/hop-orchestrator "Add user profile management with avatar upload"
```
- Backend API (gpt-5)
- Frontend UI (claude-sonnet-4)
- Tests (gpt-5-mini)
- Docs (claude-3-haiku)
- All complete in ~10 minutes

### Workflow: Production Prep
```bash
/hop-multi-task optimize
```
- Performance optimization
- Code refactoring
- Dead code cleanup
- Pattern modernization
- Ready in ~8 minutes

## 🎨 Creating Custom LOPs

Create your own LOP template in `.claude/commands/lops/`:

```markdown
# LOP: [Task Name]

## Task
[Specific task description]

## Prompt Template
```
[Detailed prompt for the agent]
```

## Suggested Agents
- **Primary:** @nano-agent-[model]
- **Alternative:** @nano-agent-[model]

## Expected Output
[What the agent should produce]

## Success Criteria
- ✅ [Criterion 1]
- ✅ [Criterion 2]
```

## 💡 Best Practices

1. **Task Independence**: Ensure parallel tasks don't conflict
2. **Model Matching**: Use appropriate models for task complexity
3. **Clear Boundaries**: Define specific scopes for each agent
4. **Result Synthesis**: Plan how to combine outputs
5. **Cost Awareness**: Mix cloud and local models for optimization

## 🚦 Troubleshooting

### Issue: Agents timing out
**Solution**: Break complex tasks into smaller LOPs

### Issue: Conflicting outputs
**Solution**: Define clearer task boundaries

### Issue: High costs
**Solution**: Use local models (gpt-oss) for simple tasks

### Issue: Slow execution
**Solution**: Reduce parallel agent count or use faster models

## 📈 Metrics & Monitoring

Track your multi-agent workflows:
- Total execution time
- Tokens used per agent
- Cost per workflow
- Success rate
- Time saved vs sequential

## 🔗 Integration

### Claude Code
1. Install nano-agent MCP server
2. Configure `.mcp.json`
3. Use `/hop-*` commands or `@agent-nano-agent-*` directly

### Cursor
1. Set up nano-agent integration
2. Use command palette for HOP commands
3. Execute parallel agents through the interface

## 🎯 Example: Complete Project Analysis

```bash
# Launch this HOP command:
/hop-orchestrator "Perform complete analysis of the nano-agent project including security, performance, documentation gaps, and improvement opportunities"

# This will automatically spawn:
# - Security scanner (gpt-5)
# - Performance analyzer (claude-opus-4-1)  
# - Documentation reviewer (claude-sonnet-4)
# - Code quality checker (gpt-5-mini)
# - Architecture analyst (gpt-oss-120b)

# All complete in ~10 minutes with comprehensive report
```

## Next Steps

1. Try the `/hop-multi-task analyze` command on your code
2. Create custom LOPs for your specific needs
3. Experiment with different agent combinations
4. Measure time savings in your workflow
5. Share your patterns with the team

---

**Remember**: The power of HOP/LOP is in parallel execution. What took hours sequentially now takes minutes in parallel! 🚀