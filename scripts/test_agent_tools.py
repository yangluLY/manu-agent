import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from agent.factory import create_manu_agent
from services.database.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        agent = create_manu_agent(db)

        print(
            agent.registry.tool_names
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()