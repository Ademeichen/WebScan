from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "vulnerability_kb" ADD "source" VARCHAR(50) /* 数据源（seebug, exploit-db等） */;
        ALTER TABLE "vulnerability_kb" ADD "has_poc" INTNOT NULL DEFAULT 0 /* 是否有POC */;
        ALTER TABLE "vulnerability_kb" ADD "ssvid" INT /* Seebug SSVID */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "vulnerability_kb" DROP COLUMN "source";
        ALTER TABLE "vulnerability_kb" DROP COLUMN "has_poc";
        ALTER TABLE "vulnerability_kb" DROP COLUMN "ssvid";"""
