from typing import List

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from flow_researcher.tools import (
    TickerToCikTool,
    GetCompanyProfileTool,
    GetKeyFinancialSeriesTool,
    GetCompanyFactsTool,
    GetLatest10qOr10kTool,
    GetCompanySubmissionsTool,
    GetLatestFilingTool,
)


@CrewBase
class FinancialAnalystCrew:
    """Financial Analyst Crew for analyzing company financial data."""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],  # type: ignore[index]
            tools=[
                TickerToCikTool(),
                GetCompanyProfileTool(),
                GetKeyFinancialSeriesTool(),
                GetCompanyFactsTool(),
                GetLatest10qOr10kTool(),
            ],
            llm=LLM(model="gemini/gemini-2.0-flash-exp"),
        )

    @agent
    def research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["research_analyst"],  # type: ignore[index]
            tools=[
                GetCompanyProfileTool(),
                GetCompanySubmissionsTool(),
                GetLatestFilingTool(),
            ],
            llm=LLM(model="gemini/gemini-2.0-flash-exp"),
        )

    @task
    def analyze_company_profile(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_company_profile"],  # type: ignore[index]
        )

    @task
    def analyze_financial_metrics(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_financial_metrics"],  # type: ignore[index]
        )

    @task
    def synthesize_financial_snapshot(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_financial_snapshot"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Financial Analyst Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
