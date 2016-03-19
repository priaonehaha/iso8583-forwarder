from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    )
import sys
sys.path[0:0] = ['/usr/share/opensipkd/modules']
from base_models import (
    Base,
    CommonModel,
    )


class JenisLog(CommonModel, Base):
    __tablename__ = 'jenis_log'
    id = Column(Integer, primary_key=True)
    nama = Column(String(16), nullable=False, unique=True)

class Log(CommonModel, Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    #jenis_id = Column(Integer, ForeignKey('jenis_log.id'), nullable=False)
    tgl = Column(DateTime(timezone=True), nullable=False)
    ip = Column(String(15), nullable=False)
    #kirim = Column(Boolean, nullable=False)
    #raw = Column(Text, nullable=False)
    #method = Column(String(16), nullable=False)
    #ref_id = Column(Integer, ForeignKey('log.id'))
    invoice_no = Column(String(64))
    ntb        = Column(String(16))
    ntp        = Column(String(16))
    amount     = Column(String(16))
    bank_id    = Column(String(16))
    bit_001    = Column(Text)
    bit_002    = Column(Text)
    bit_003    = Column(Text)
    bit_004    = Column(Text)
    bit_005    = Column(Text)
    bit_006    = Column(Text)
    bit_007    = Column(Text)
    bit_008    = Column(Text)
    bit_009    = Column(Text)
    bit_010    = Column(Text)
    bit_011    = Column(Text)
    bit_012    = Column(Text)
    bit_013    = Column(Text)
    bit_014    = Column(Text)
    bit_015    = Column(Text)
    bit_016    = Column(Text)
    bit_017    = Column(Text)
    bit_018    = Column(Text)
    bit_019    = Column(Text)
    bit_020    = Column(Text)
    bit_021    = Column(Text)
    bit_022    = Column(Text)
    bit_023    = Column(Text)
    bit_024    = Column(Text)
    bit_025    = Column(Text)
    bit_026    = Column(Text)
    bit_027    = Column(Text)
    bit_028    = Column(Text)
    bit_029    = Column(Text)
    bit_030    = Column(Text)
    bit_031    = Column(Text)
    bit_032    = Column(Text)
    bit_033    = Column(Text)
    bit_034    = Column(Text)
    bit_035    = Column(Text)
    bit_036    = Column(Text)
    bit_037    = Column(Text)
    bit_038    = Column(Text)
    bit_039    = Column(Text)
    bit_040    = Column(Text)
    bit_041    = Column(Text)
    bit_042    = Column(Text)
    bit_043    = Column(Text)
    bit_044    = Column(Text)
    bit_045    = Column(Text)
    bit_046    = Column(Text)
    bit_047    = Column(Text)
    bit_048    = Column(Text)
    bit_049    = Column(Text)
    bit_050    = Column(Text)
    bit_051    = Column(Text)
    bit_052    = Column(Text)
    bit_053    = Column(Text)
    bit_054    = Column(Text)
    bit_055    = Column(Text)
    bit_056    = Column(Text)
    bit_057    = Column(Text)
    bit_058    = Column(Text)
    bit_059    = Column(Text)
    bit_060    = Column(Text)
    bit_061    = Column(Text)
    bit_062    = Column(Text)
    bit_063    = Column(Text)
    bit_064    = Column(Text)
    bit_065    = Column(Text)
    bit_066    = Column(Text)
    bit_067    = Column(Text)
    bit_068    = Column(Text)
    bit_069    = Column(Text)
    bit_070    = Column(Text)
    bit_071    = Column(Text)
    bit_072    = Column(Text)
    bit_073    = Column(Text)
    bit_074    = Column(Text)
    bit_075    = Column(Text)
    bit_076    = Column(Text)
    bit_077    = Column(Text)
    bit_078    = Column(Text)
    bit_079    = Column(Text)
    bit_080    = Column(Text)
    bit_081    = Column(Text)
    bit_082    = Column(Text)
    bit_083    = Column(Text)
    bit_084    = Column(Text)
    bit_085    = Column(Text)
    bit_086    = Column(Text)
    bit_087    = Column(Text)
    bit_088    = Column(Text)
    bit_089    = Column(Text)
    bit_090    = Column(Text)
    bit_091    = Column(Text)
    bit_092    = Column(Text)
    bit_093    = Column(Text)
    bit_094    = Column(Text)
    bit_095    = Column(Text)
    bit_096    = Column(Text)
    bit_097    = Column(Text)
    bit_098    = Column(Text)
    bit_099    = Column(Text)
    bit_100    = Column(Text)
    bit_101    = Column(Text)
    bit_102    = Column(Text)
    bit_103    = Column(Text)
    bit_104    = Column(Text)
    bit_105    = Column(Text)
    bit_106    = Column(Text)
    bit_107    = Column(Text)
    bit_108    = Column(Text)
    bit_109    = Column(Text)
    bit_110    = Column(Text)
    bit_111    = Column(Text)
    bit_112    = Column(Text)
    bit_113    = Column(Text)
    bit_114    = Column(Text)
    bit_115    = Column(Text)
    bit_116    = Column(Text)
    bit_117    = Column(Text)
    bit_118    = Column(Text)
    bit_119    = Column(Text)
    bit_120    = Column(Text)
    bit_121    = Column(Text)
    bit_122    = Column(Text)
    bit_123    = Column(Text)
    bit_124    = Column(Text)
    bit_125    = Column(Text)
    bit_126    = Column(Text)
    bit_127    = Column(Text)
    bit_128    = Column(Text)
    
    @classmethode
    def save(self,bits=[]):
        log = cls()
        log.to_dict(bits)
        DBSession.add(log)
        DBSession.flush()
        DBSession.commit()
        
class LogValues(CommonModel, Base):
    __tablename__ = 'log_values'
    id = Column(Integer, primary_key=True)
    ref_id = Column(Integer, ForeignKey('log.id'), nullable=False)
    key = Column(String(16), nullable=False)
    value = Column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint('ref_id', 'key'),
        )