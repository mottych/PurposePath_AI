"""AWS Step Functions client for enrichment orchestration.

This client provides integration with AWS Step Functions for complex
enrichment workflows that may involve multiple data sources.
"""

from typing import Any

import structlog

logger = structlog.get_logger()


class StepFunctionsClient:
    """
    Client for AWS Step Functions integration.

    This client provides methods to execute Step Functions for
    enrichment workflows, particularly for complex multi-step
    data gathering from various business systems.

    Design:
        - Async execution support
        - Status polling
        - Error handling and retries
        - Mock-friendly for testing
    """

    def __init__(self, step_functions_client: Any, state_machine_arn: str):
        """
        Initialize Step Functions client.

        Args:
            step_functions_client: Boto3 Step Functions client
            state_machine_arn: ARN of the enrichment state machine
        """
        self.client = step_functions_client
        self.state_machine_arn = state_machine_arn
        logger.info("Step Functions client initialized", state_machine_arn=state_machine_arn)

    async def start_enrichment_execution(
        self, execution_input: dict[str, Any], execution_name: str | None = None
    ) -> str:
        """
        Start a Step Functions execution for enrichment.

        Args:
            execution_input: Input data for the state machine
            execution_name: Optional execution name (auto-generated if None)

        Returns:
            Execution ARN

        Raises:
            Exception: If execution fails to start
        """
        try:
            import json

            response = self.client.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=execution_name,
                input=json.dumps(execution_input),
            )

            execution_arn = response["executionArn"]

            logger.info(
                "Step Functions execution started",
                execution_arn=execution_arn,
                execution_name=execution_name,
            )

            return execution_arn

        except Exception as e:
            logger.error("Failed to start Step Functions execution", error=str(e))
            raise

    async def get_execution_result(
        self, execution_arn: str, timeout_seconds: int = 30
    ) -> dict[str, Any]:
        """
        Get execution result (with polling).

        Args:
            execution_arn: Execution ARN to check
            timeout_seconds: Maximum time to wait for completion

        Returns:
            Execution output as dict

        Raises:
            TimeoutError: If execution doesn't complete in time
            Exception: If execution fails
        """
        import asyncio
        import json
        import time

        start_time = time.time()

        try:
            while True:
                response = self.client.describe_execution(executionArn=execution_arn)

                status = response["status"]

                if status == "SUCCEEDED":
                    output = json.loads(response["output"])
                    logger.info("Step Functions execution succeeded", execution_arn=execution_arn)
                    return output

                elif status in ["FAILED", "TIMED_OUT", "ABORTED"]:
                    error = response.get("error", "Unknown error")
                    logger.error(
                        "Step Functions execution failed",
                        execution_arn=execution_arn,
                        status=status,
                        error=error,
                    )
                    raise Exception(f"Execution {status}: {error}")

                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    logger.error(
                        "Step Functions execution timed out",
                        execution_arn=execution_arn,
                        timeout=timeout_seconds,
                    )
                    raise TimeoutError(
                        f"Execution did not complete within {timeout_seconds} seconds"
                    )

                # Wait before polling again
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(
                "Failed to get execution result", execution_arn=execution_arn, error=str(e)
            )
            raise

    async def execute_and_wait(
        self, execution_input: dict[str, Any], timeout_seconds: int = 30
    ) -> dict[str, Any]:
        """
        Execute and wait for result (convenience method).

        Args:
            execution_input: Input data for the state machine
            timeout_seconds: Maximum time to wait

        Returns:
            Execution output

        Raises:
            TimeoutError: If execution doesn't complete in time
            Exception: If execution fails
        """
        execution_arn = await self.start_enrichment_execution(execution_input)
        result = await self.get_execution_result(execution_arn, timeout_seconds)
        return result


__all__ = ["StepFunctionsClient"]
