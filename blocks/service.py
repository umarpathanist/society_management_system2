from flask import abort
from blocks.repository import BlockRepository
from societies.service import SocietyService
from database.connection import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor





class BlockService:

    @staticmethod
    def get_by_id(block_id):
        return BlockRepository.get_by_id(block_id)

    @staticmethod
    def create(data):
        return BlockRepository.create(data)

    @staticmethod
    def update(block_id, data):
        return BlockRepository.update(block_id, data)

    @staticmethod
    def delete(block_id):
        return BlockRepository.delete(block_id)

    @staticmethod
    def list_blocks_for_society(society_id):
        society = SocietyService.get_by_id(society_id)
        if not society:
            abort(404, "Society not found")

        blocks = BlockRepository.get_blocks_by_society(society_id)
        return society, blocks



    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                b.id,
                b.name,
                COUNT(f.id) AS total_flats
            FROM blocks b
            LEFT JOIN flats f ON f.block_id = b.id
            WHERE b.society_id = %s
            GROUP BY b.id
            ORDER BY b.id
        """, (society_id,))

        blocks = cur.fetchall()
        cur.close()
        conn.close()
        return blocks
