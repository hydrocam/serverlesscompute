import psycopg2
from config import db_host, db_name, db_user, db_password

def write_to_database(timestamp, ROI, segmented_timestamp, segmented_bucket_path, site_id,
                      event_timestamp, upload_timestamp, image_bucket_path, image_md5,stage,
                      iou_score=None, seg_verify=False, original_image_url=None, segmented_image_url=None):
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cur = conn.cursor()
    insert_query = """
        INSERT INTO images_segmented 
        (site_id, image_path, image_timestamp, image_md5, event_timestamp, upload_timestamp, 
         segmented_path, segmented_timestamp, roi, iou_score, segmentation_verification,
         original_image_url, segmented_image_url, stage_m)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    cur.execute(insert_query, (
        site_id,
        image_bucket_path,
        timestamp,
        image_md5,
        event_timestamp,
        upload_timestamp,
        segmented_bucket_path,
        segmented_timestamp,
        ROI,
        iou_score,
        seg_verify,
        original_image_url,
        segmented_image_url,
        stage
    ))
    inserted_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return inserted_id
