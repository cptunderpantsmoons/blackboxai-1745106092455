from learning_loop import AutonomousGenie

class MCPAwareAutonomousGenie(AutonomousGenie):
    def __init__(self, mcp_orchestrator):
        super().__init__()
        self.mcp = mcp_orchestrator
        self.context_memory = HierarchicalContextStore()

    async def generate_innovation(self, operational_context: dict):
        # Generate MCP-compliant context packet
        mcp_packet = await self.mcp.generate_mcp_compliant_attack(operational_context)
        
        # Retrieve relevant historical context
        similar_contexts = await self.context_memory.query(
            mcp_packet.payload.context_window
        )
        
        # Generate innovation using MCP-bound context
        innovation = await super().generate_innovation({
            'current': mcp_packet.payload.context_window,
            'historical': similar_contexts
        })
        
        # Apply MCP constraints to generated ideas
        return [self._apply_mcp_guardrails(idea) for idea in innovation]

    def _apply_mcp_guardrails(self, concept: dict) -> dict:
        """Enforce MCP protocol rules on generated concepts"""
        return {
            **concept,
            'execution_parameters': self._constrain_by_mcp_class(
                concept['execution_parameters'],
                concept['context_class']
            )
        }
