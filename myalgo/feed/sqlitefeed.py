import datetime
import time

from sqlalchemy import Column, DateTime, String, Integer, Float, CHAR, func
from sqlalchemy import and_
from sqlalchemy import cast
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from myalgo.bar.bar import Bar
from myalgo.feed.barfeed import BarFeed
from myalgo.logger import get_logger

Base = declarative_base()


def make_bar_model(table_name):
    class BarModel(Base):
        __tablename__ = table_name
        id = Column(Integer, primary_key=True)
        type = Column(CHAR(45))

        ask_open = Column(Float)
        ask_low = Column(Float)
        ask_high = Column(Float)
        ask_close = Column(Float)

        bid_open = Column(Float)
        bid_low = Column(Float)
        bid_high = Column(Float)
        bid_close = Column(Float)

        start_date = Column(DateTime)
        end_date = Column(DateTime)

        def convert_to_bar(self):
            return Bar(self.start_date, self.end_date, self.ask_open, self.ask_close, self.ask_high, self.ask_low,
                       self.bid_open, self.bid_close, self.bid_high, self.bid_low, 0)

    return BarModel


class SQLiteFeed(BarFeed):
    LOGGER_NAME = "SQLITE_FEED_LOGGER"

    def __init__(self,
                 table_name='bins',
                 file_name='sqlite'):
        self.__engine = create_engine(f'sqlite:///{file_name}')
        self.__DBSession = sessionmaker(bind=self.__engine)
        self.__logger = get_logger(SQLiteFeed.LOGGER_NAME)
        self.__bar_model = make_bar_model(table_name)

        def before_cursor_execute(conn, cursor, statement,
                                  parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())

            self.__logger.debug(f'Start Query: {statement} with params: {parameters}')

        def after_cursor_execute(conn, cursor, statement,
                                 parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            self.__logger.debug("Query Complete!")
            self.__logger.debug("Total Time: %f", total)

        event.listens_for(self.__engine, "before_cursor_execute")(before_cursor_execute)
        event.listens_for(self.__engine, "after_cursor_execute")(after_cursor_execute)

        super(SQLiteFeed, self).__init__()

        self.bars = []

    @property
    def new_session(self):
        return self.__DBSession()

    @property
    def model(self):
        return self.__bar_model

    def load_data(self, instruments, from_date, to_date):
        """将数据全部加载上来"""

        self.__logger.debug(
            f'loading data from database, for instruments: {instruments} from: {from_date} to: {to_date}')
        data_dicts = {}

        length = []
        session = self.new_session

        for instrument in instruments:
            data_dicts[instrument] = self.__fetch(session, instrument, to_date, from_date)
            length.append(len(data_dicts[instrument]))

        session.close()

        self.__logger.info('loading data from database complete!')

        m_length = min(length)

        def get_instrument(i):
            new_dicts = {}
            for inst in instruments:
                new_dicts[inst] = data_dicts[inst][i].convert_to_bar()
            return new_dicts

        result = [get_instrument(i) for i in range(m_length)]

        self.bars = result

    def __fetch(self, session, instrument, to_date=datetime.datetime(2019, 1, 1, 0, 0, 0),
                from_date=datetime.datetime(2012, 1, 1, 0, 0, 0)):
        """
            选择一段时间的交易记录，并且返回
            from_date: 开始时间
            to_date: 结束时间
            type: 种类
        """
        cursor = session.query(self.model).filter(and_(
            cast(self.model.type, String) == cast(instrument, String),
            self.model.start_date >= func.datetime(from_date),
            self.model.end_date <= func.datetime(to_date))).order_by("start_date")
        result = cursor.all()
        return result
