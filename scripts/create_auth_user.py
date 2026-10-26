
import argparse
import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from services.auth.security import hash_password
from services.database.models.user import User
from services.database.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--username",
        required=True,
    )

    parser.add_argument(
        "--role",
        choices=[
            "viewer",
            "workflow_approver",
        ],
        default="viewer",
    )

    args = parser.parse_args()

    username = args.username.strip()

    if not username:
        raise ValueError("用户名不能为空")

    password = getpass.getpass(
        "请输入密码（至少12位）："
    )

    confirm = getpass.getpass(
        "再次输入密码："
    )

    if password != confirm:
        raise ValueError("两次密码不一致")

    password_hash = hash_password(password)

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(
                User.username == username
            )
        )

        if existing is not None:
            raise ValueError("用户名已存在")

        user = User(
            username=username,
            password_hash=password_hash,
            role=args.role,
            is_active=True,
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "用户名已存在"
            ) from None

        db.refresh(user)

        print(
            f"创建成功：id={user.id}, "
            f"username={user.username}, "
            f"role={user.role}"
        )


if __name__ == "__main__":
    main()
