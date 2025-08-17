import logging
from typing import AsyncGenerator, Dict

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools.retriever import create_retriever_tool

from app.agents.tools import get_current_time
from app.core.prompts import AGENT_SYSTEM_PROMPT
from app.services.chat_service import ChatService, get_chat_service

logger = logging.getLogger(__name__)

class AgentService:
    """
    Asynchronous service to handle the advanced, tool-calling voice agent.
    """
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        self.agent_executor = self._create_agent_executor()

    def _create_agent_executor(self) -> RunnableWithMessageHistory:
        """Creates the agent executor with memory and tools."""
        retriever_tool = create_retriever_tool(
            self.chat_service.retriever,
            "search_portofolio_knowledge_base",
            "Searches and returns information about Fadhil Ahmad Hidayat's skills, experience, and projects.",
        )
        tools = [get_current_time, retriever_tool]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", AGENT_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        
        agent = create_tool_calling_agent(self.chat_service.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        return RunnableWithMessageHistory(
            agent_executor,
            self.chat_service.get_session_history, # Reuse memory from ChatService
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    async def stream_agent_response(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[Dict, None]:
        """
        Streams the response from the agent, yielding events for each step.
        """
        if not self.agent_executor:
            yield {"event": "error", "data": "Agent not initialized."}
            return

        config = {"configurable": {"session_id": session_id}}
        
        async for event in self.agent_executor.astream_events(
            {"input": message}, config=config, version="v1"
        ):
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                yield {"event": "token", "data": event["data"]["chunk"].content}
            elif kind == "on_tool_start":
                logger.info(f"Tool started: {event['name']}")
                yield {"event": "tool_start", "data": event["name"]}
            elif kind == "on_tool_end":
                logger.info(f"Tool ended: {event['name']}")
                yield {"event": "tool_end", "data": event["name"]}

_agent_service_instance: AgentService | None = None

def get_agent_service() -> AgentService:
    global _agent_service_instance
    if _agent_service_instance is None:
        chat_service = get_chat_service()
        _agent_service_instance = AgentService(chat_service)
    return _agent_service_instance