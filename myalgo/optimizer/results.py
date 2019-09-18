from sqlalchemy import Column, String, Integer, Float
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class ResultModel(Base):
    __tablename__ = "result_image"
    id = Column(Integer, primary_key=True)

    ##
    ## 这里只支持两个参数。。
    ## 因为参数过多的都不太好
    p1 = Column(Float)
    p2 = Column(Float)

    strategy_name = Column(String)
    win_rate = Column(Float)
    sharp_ratio = Column(Float)
    profit_rate = Column(Float)
    ret = Column(Float)
    draw_down = Column(Float)
    # 回撤时长，按分钟计算
    draw_down_duration = Column(Integer)
    trade_count = Column(Integer)
    plr = Column(Float)


class ResultManager:
    def __init__(self,
                 strategy_name: str,
                 file_name='result.sqlite'):
        self.__engine = create_engine(f'sqlite:///{file_name}')
        Base.metadata.create_all(self.__engine)
        self.__DBSession = Session(self.__engine)

        self.__strategy_name = strategy_name

    """
        Here we save the data into the sqlite
        
    """

    def save(self, p1, p2, win_rate, sharp_ratio, profit_rate,
             ret, draw_down, draw_down_duration, trade_count, plr):
        result = ResultModel(p1=p1, p2=p2, strategy_name=self.__strategy_name, win_rate=win_rate,
                             sharp_ratio=sharp_ratio, profit_rate=profit_rate, ret=ret, draw_down=draw_down,
                             draw_down_duration=draw_down_duration.total_seconds() / 60, trade_count=trade_count,
                             plr=plr,
                             )

        try:
            self.__DBSession.add(result)
            self.__DBSession.commit()
        except Exception as e:
            print(e)
            self.__DBSession.rollback()

    def load(self):
        cursor = self.__DBSession.query(ResultModel).filter(ResultModel.strategy_name == self.__strategy_name)
        return cursor.all()

    def strategy_name(self):
        return self.__strategy_name
