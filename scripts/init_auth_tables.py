
from services.database.models.user import User
from services.database.session import engine


def main():
    User.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    print("auth_users 表初始化成功")


if __name__ == "__main__":
    main()
