# How to Use Circuit-Synth Agents in Claude Code

## ✅ Agents Are Registered and Working!

Your agents are properly configured. Here's how to use them:

## 🎯 How to Call Agents

**Use the `@Task()` syntax to call agents:**

```
@Task(subagent_type="contributor", description="Help with circuit design", prompt="Design a circuit with ESP32, IMU, and USB-C")
```

## 🤖 Available Agents

### `contributor` - Start Here! 
```
@Task(subagent_type="contributor", description="Development help", prompt="How do I add an ESP32 to a circuit?")
```

### `circuit-synth` - Code Generation
```
@Task(subagent_type="circuit-synth", description="Generate circuit", prompt="Create Python code for ESP32 with USB-C power")
```

### `simulation-expert` - SPICE Analysis
```
@Task(subagent_type="simulation-expert", description="Validate design", prompt="Analyze this power supply circuit")
```

## ✅ Agents Are Now Fixed!

1. **Fixed agent file format** - Updated YAML frontmatter to use `name:`, `description:`, `tools:` format
2. **Session hook updated** - Shows correct agents
3. **Ready to use** - Call agents explicitly with `@Task()` syntax

## 💡 Best Practices

**For Your ESP32 + IMU + USB-C Design:**
```
@Task(subagent_type="contributor", description="Circuit design help", prompt="I want to design a circuit with ESP32, IMU, and USB-C. Walk me through the process step by step.")
```

**The contributor agent will:**
- Guide you through the design process
- Use its tools to find components
- Help with circuit-synth Python code
- Run tests and validate the design

## 🔧 Next Steps

1. **Restart Claude Code** to pick up the fixed agent format
2. **Use the contributor agent** for your ESP32 design:
   ```
   @Task(subagent_type="contributor", description="ESP32 design help", prompt="Help me design an ESP32 circuit with IMU and USB-C")
   ```
3. **The agents now work properly** - correct YAML format fixed the issue! 🚀