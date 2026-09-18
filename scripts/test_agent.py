# scripts/test_agent.py

import logging

from agent.factory import create_manu_agent
from services.database.session import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main():

    # SessionLocal 名字如果和你的项目不一样，
    # 改成你 V0 当前创建数据库 Session 的方法。
    with SessionLocal() as db:

        agent = create_manu_agent(db)

        questions = [
            "CNC-001 当前是什么状态？",
            "系统里现在有哪些设备？",
            "CNC-001 当前有没有报警？",
            "目前有哪些低库存物料？",
            "现在有哪些未完成的生产工单？",
        ]

        for question in questions:

            print("\n" + "=" * 70)
            print(f"用户：{question}")
            print("-" * 70)

            try:
                answer = agent.chat(question)

                print(f"ManuAgent：{answer}")

            except Exception as exc:
                logging.exception(  # noqa: LOG015
                    "Agent test failed: %s",
                    exc,  # noqa: TRY401
                )


if __name__ == "__main__":
    main()