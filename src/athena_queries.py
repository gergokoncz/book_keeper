CREATE_USER_TABLE_QUERY = """
CREATE EXTERNAL TABLE IF NOT EXISTS `book_keeper`.`{}_books` (
  `book_id` int,
  `title` string,
  `subtitle` string,
  `author` string,
  `location` string,
  `pageN` int,
  `pageCurrent` int,
  `currentDate` timestamp,
  `finishDate` timestamp,
  `tag1` string,
  `tag2` string,
  `tag3` string,
  `language` string,
  `slug` string
)
PARTITIONED BY (`run_date` date)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://book-keeper-store-bucket/{}/books/'
TBLPROPERTIES (
  'classification' = 'parquet'
);
"""

UPDATE_USER_TABLE_QUERY = """
MSCK REPAIR TABLE `book_keeper.{}`;
"""

CREATE_LATEST_UPDATE_BER_BOOK_QUERY = """
CREATE OR REPLACE VIEW book_keeper.{}_latest_update_per_book AS
SELECT slug, MAX(currentDate) as latestEditDate
FROM book_keeper.{}_books
GROUP BY slug;
"""

READ_USER_TABLE_QUERY = """
SELECT * FROM `book_keeper.{}_books`;
"""
