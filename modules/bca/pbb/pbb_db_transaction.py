import sys
import traceback
from StringIO import StringIO
from random import randrange
from types import DictType
from ISO8583.ISO8583 import ISO8583
from models import (
    Invoice,
    Pembayaran,
    Kelurahan,
    Kecamatan,
    Kabupaten,
    Propinsi,
    )

from datetime import datetime


sys.path[0:0] = ['/usr/share/opensipkd/modules']
from tools import FixLength
from base_models import DBSession
sys.path[0:0] = ['/etc/opensipkd']
from pbb_conf import (
    host,
    is_update_sppt,
    nip_rekam_byr_sppt,
    )
sys.path[0:0] = ['/usr/share/opensipkd-forwarder/modules/bca/']
from pbb import PbbDbSession

sys.path[0:0] = ['/usr/share/opensipkd-forwarder/modules/bca']
from pbb_structure import INVOICE_ID, INVOICE_PROFILE
from CalculateInvoice import (
    CalculateInvoice,
    query_sppt,
    )
    
from DbTools import query_pembayaran

#from pbb_models import (
#    INQUIRY_SEQ,
#    Payment,
#    Reversal,
#    )

def cari_kelurahan(propinsi, kabupaten, kecamatan, kelurahan):
    q = PbbDbSession.query(Kelurahan).filter_by(
            kd_propinsi=propinsi,
            kd_dati2=kabupaten,
            kd_kecamatan=kecamatan,
            kd_kelurahan=kelurahan)
    r = q.first()
    return r and r.nm_kelurahan or ''

def cari_kecamatan(propinsi, kabupaten, kecamatan):
    q = PbbDbSession.query(Kecamatan).filter_by(
            kd_propinsi=propinsi,
            kd_dati2=kabupaten,
            kd_kecamatan=kecamatan)
    r = q.first()
    return r and r.nm_kecamatan or ''

def cari_propinsi(propinsi):
    q = PbbDbSession.query(Propinsi).filter_by(kd_propinsi=propinsi)
    r = q.first()
    return r and r.nm_propinsi or ''

def nama_jalan_op(sppt):
    return sppt.jln_wp_sppt

# def inquiry_id():
    # return INQUIRY_SEQ.execute(DBSession.bind)

def create_payment_id(prefix):
    max_loop = 10
    loop = 0
    while True:
        acak = randrange(11111111, 99999999)
        acak = str(acak)
        trx_id = ''.join([prefix, acak])
        print('Check Trx ID %s' % trx_id)
        q = DBSession.query(Payment).filter_by(id=trx_id)
        found = q.first()
        if not found:
            return trx_id
        loop += 1
        if loop == max_loop:
            print('*** Max loop for create payment ID. Call your programmer please.')
            return

# def pay2invoice_id(pay):
    # return ''.join([pay.propinsi, pay.kabupaten, pay.kecamatan,
        # pay.kelurahan, pay.blok, pay.urut, pay.jenis, str(pay.tahun)])

def inq2bayar(invoice_id):
    q = query_pembayaran(invoice_id['Propinsi'],
            invoice_id['Kabupaten'],
            invoice_id['Kecamatan'],
            invoice_id['Kelurahan'],
            invoice_id['Blok'],
            invoice_id['Urut'],
            invoice_id['Jenis'],
            invoice_id['Tahun Pajak'])
            
    q = q.order_by('pembayaran_sppt_ke DESC')
    return q.first()
    
class MyFixLength(FixLength):
    def get(self, name):
        return self.fields[name]['value'] or None

FIELD_BANK = ['kd_kanwil', 'kd_kantor', 'kd_tp']
FIELD_BANK_NON_TP = FIELD_BANK[:-1]

class PbbDbTransaction(): #
    def __init__(self, *args, **kwargs):
        self.invoice_id = MyFixLength(INVOICE_ID)
        self.invoice_id_raw = None # Cache
        self.invoice_profile = MyFixLength(INVOICE_PROFILE)
        if 'invoice_id' in kwargs:
            self.invoice_id_raw = kwargs['invoice_id']
        if 'conf' in kwargs:
            self.conf = kwargs['conf']
        if 'channel' in kwargs:
            self.channel = kwargs['channel']
        #Transaction.__init__(self, *args, **kwargs)

    def get_invoice(self):
        #self.invoice_id_raw = invoice_id_raw
        if not self.invoice_id.set_raw(self.invoice_id_raw):
            return self.ack_invalid_number()
        self.invoice_id2profile()
        
        self.calc = CalculateInvoice(
            self.invoice_id['Propinsi'],
            self.invoice_id['Kabupaten'],
            self.invoice_id['Kecamatan'],
            self.invoice_id['Kelurahan'],
            self.invoice_id['Blok'],
            self.invoice_id['Urut'],
            self.invoice_id['Jenis'],
            self.invoice_id['Tahun Pajak'])
            
        if self.calc.invoice:
            inv = self.calc.invoice
            self.invoice_profile.from_dict({
                'Nama': inv.nm_wp_sppt,
                'Luas Tanah': int(inv.luas_bumi_sppt),
                'Luas Bangunan': int(inv.luas_bng_sppt),
                'Lokasi': nama_jalan_op(inv),
                'Jatuh Tempo': inv.tgl_jatuh_tempo_sppt.strftime('%d%m%Y'),
                'Tagihan': self.calc.tagihan,
                'Denda': self.calc.denda,
                'Total Bayar': self.calc.total})
            self.calc.invoice_profile=self.invoice_profile
            #self.channel = self.get_channel()
        return self.calc

    def invoice_id2profile(self):
        nama_kelurahan = self.nama_kelurahan()
        nama_kecamatan = self.nama_kecamatan()
        nama_propinsi = self.nama_propinsi()
        self.invoice_profile.from_dict({
            'Propinsi': self.invoice_id['Propinsi'],
            'Kabupaten': self.invoice_id['Kabupaten'],
            'Kecamatan': self.invoice_id['Kecamatan'],
            'Kelurahan': self.invoice_id['Kelurahan'],
            'Blok': self.invoice_id['Blok'],
            'Urut': self.invoice_id['Urut'],
            'Jenis': self.invoice_id['Jenis'],
            'Tahun Pajak': self.invoice_id['Tahun Pajak'],
            'Nama Kelurahan': nama_kelurahan,
            'Nama Kecamatan': nama_kecamatan,
            'Nama Propinsi': nama_propinsi})

    ###########
    # Profile #
    ###########
    def nama_kelurahan(self):
        return cari_kelurahan(
            self.invoice_id['Propinsi'],
            self.invoice_id['Kabupaten'],
            self.invoice_id['Kecamatan'],
            self.invoice_id['Kelurahan'])

    def nama_kecamatan(self):
        return cari_kecamatan(
            self.invoice_id['Propinsi'],
            self.invoice_id['Kabupaten'],
            self.invoice_id['Kecamatan'])

    def nama_propinsi(self):
        return cari_propinsi(self.invoice_id['Propinsi'])

    def create_payment(self, total_bayar,transaction_date):
        self.transaction_date = transaction_date
        bayar, urutan_bayar = self.bayar(total_bayar)
        return bayar
        
    def bayar(self, total_bayar):
        inv = self.calc.invoice
        bayar = inq2bayar(self.invoice_id)
        if bayar:
            ke = bayar.pembayaran_sppt_ke + 1
        else:
            ke = 1
        bayar = Pembayaran()
        bayar.kd_propinsi = inv.kd_propinsi #self.invoice_id['Propinsi']
        bayar.kd_dati2 = inv.kd_dati2 #self.invoice_id['Kabupaten']
        bayar.kd_kecamatan = inv.kd_kecamatan #self.invoice_id['Kecamatan']
        bayar.kd_kelurahan = inv.kd_kelurahan #self.invoice_id['Kelurahan']
        bayar.kd_blok = inv.kd_blok #self.invoice_id['Blok']
        bayar.no_urut = inv.no_urut #self.invoice_id['Urut']
        bayar.kd_jns_op = inv.kd_jns_op #self.invoice_id['Jenis']
        bayar.thn_pajak_sppt = inv.thn_pajak_sppt #self.invoice_id['Tahun Pajak']
        bayar.pembayaran_sppt_ke = ke
        bayar.tgl_rekam_byr_sppt = datetime.now()
        bayar.tgl_pembayaran_sppt = self.transaction_date
        bayar.jml_sppt_yg_dibayar = self.calc.total #total_bayar 
        bayar.denda_sppt = self.calc.denda #inq.denda
        bayar.nip_rekam_byr_sppt = nip_rekam_byr_sppt
        for fieldname in FIELD_BANK:
            value = self.conf[fieldname]
            value = self.get_real_value(value)
            bayar.from_dict({fieldname: value})
        PbbDbSession.add(bayar)
        return bayar, ke


        
    def commit(self):
        PbbDbSession.flush()
        PbbDbSession.commit()
        #self.ack()
       
    def get_real_value(self, value):
        if type(value) is not DictType:
            return value
        if self.channel in value:
            return value[self.channel]
        if 'default' in value:
            return value['default']
        return '00'

    def get_field_bank(self):
        return FIELD_BANK

    def get_field_bank_non_tp(self):
        return FIELD_BANK_NON_TP

    # ############
    # # Reversal #
    # ############
    # def _reversal_response(self):
        # reversal_iso_request = ISO8583.getRawIso(self.from_iso).upper()
        # pay_iso_request = '0200' + reversal_iso_request[4:]
        # q = DBSession.query(Payment).filter_by(iso_request=pay_iso_request)
        # pay = q.first()
        # if not pay:
            # return self.ack_payment_not_found()
        # invoice_id = pay2invoice_id(pay)
        # cls = self.get_reversal_cls()
        # rev = cls(pay) 
        # if not rev.bayar:
            # return self.ack_payment_not_found_2(invoice_id, pay.ke)
        # if not rev.invoice:
            # return self.ack_not_available_2(invoice_id)
        # if not rev.is_paid():
            # return self.ack_invoice_open(invoice_id)
        # rev.set_unpaid()
        # reversal = Reversal(payment_id=pay.id) # Catatan tambahan
        # reversal.iso_request = reversal_iso_request
        # DBSession.add(rev.bayar)
        # DBSession.add(rev.invoice)
        # DBSession.add(reversal)
        # self.commit()
        # #self.settlement.set_raw(self.from_iso.get_value(13))

    # def reversal_response(self):
        # try:
            # self._reversal_response()
        # except:
            # f = StringIO()
            # traceback.print_exc(file=f)
            # self.log_error(f.getvalue())
            # f.close()
            # self.ack_other('other error')

    # def get_reversal_cls(self): # override
        # return



# def sppt2nop(sppt):
    # return sppt.kd_propinsi + sppt.kd_dati2 + sppt.kd_kecamatan + \
           # sppt.kd_kelurahan + sppt.kd_blok + sppt.no_urut + sppt.kd_jns_op




# def pay2invoice_id(pay):
    # return ''.join([pay.propinsi, pay.kabupaten, pay.kecamatan,
        # pay.kelurahan, pay.blok, pay.urut, pay.jenis, str(pay.tahun)])

# class DbTransaction():


    # def get_calc_cls(self):
        # return CalculateInvoice

    # def invoice_id2profile(self):
        # nama_kelurahan = self.nama_kelurahan()
        # nama_kecamatan = self.nama_kecamatan()
        # nama_propinsi = self.nama_propinsi()
        # self.invoice_profile.from_dict({
            # 'Propinsi': self.invoice_id['Propinsi'],
            # 'Kabupaten': self.invoice_id['Kabupaten'],
            # 'Kecamatan': self.invoice_id['Kecamatan'],
            # 'Kelurahan': self.invoice_id['Kelurahan'],
            # 'Blok': self.invoice_id['Blok'],
            # 'Urut': self.invoice_id['Urut'],
            # 'Jenis': self.invoice_id['Jenis'],
            # 'Tahun Pajak': self.invoice_id['Tahun Pajak'],
            # 'Nama Kelurahan': nama_kelurahan,
            # 'Nama Kecamatan': nama_kecamatan,
            # 'Nama Propinsi': nama_propinsi})

    # def sppt2profile(self):
        # inv = self.calc.invoice
        # self.invoice_profile.from_dict({
            # 'Nama': inv.nm_wp_sppt,
            # 'Luas Tanah': int(inv.luas_bumi_sppt),
            # 'Luas Bangunan': int(inv.luas_bng_sppt),
            # 'Lokasi': nama_jalan_op(inv)})
            
    # def create_payment(self, inq, total_bayar):
        # payment, bayar = BaseDbTransaction.create_payment(self, inq,
            # total_bayar)
        # payment.kd_kanwil_bank = self.conf['kd_kanwil'] 
        # payment.kd_kppbb_bank = self.conf['kd_kantor']
        # # 2 field ini tidak ada di tabel pembayaran_sppt
        # payment.kd_bank_tunggal = '01'
        # payment.kd_bank_persepsi = '01'
        # return payment, bayar

    # ############
    # # Reversal #
    # ############
    # def get_reversal_cls(self):
        # return PaymentReversal

    # ###########
    # # Profile #
    # ###########


    # def invoice2inquiry(self):
        # return invoice2inquiry(self.calc.invoice)

    # def invoice2payment(self):
        # return invoice2payment(self.calc.invoice)

# class PbbDBTransaction():
    # def get_invoice(self):
        # self.invoice_id_raw = self.from_iso.get_value(61).strip()
        # #IF PBB
        # #IF BPHTB
        # #IF OTHER
        # if not self.invoice_id.set_raw(self.invoice_id_raw):
            # return self.ack_invalid_number()
        # self.invoice_id2profile()
        # cls = self.get_calc_cls()
        # self.calc = cls(
            # self.invoice_id['Propinsi'],
            # self.invoice_id['Kabupaten'],
            # self.invoice_id['Kecamatan'],
            # self.invoice_id['Kelurahan'],
            # self.invoice_id['Blok'],
            # self.invoice_id['Urut'],
            # self.invoice_id['Jenis'],
            # self.invoice_id['Tahun Pajak'])
        # if not self.calc.invoice:
            # return self.ack_not_available()
        # self.sppt2profile()
        # self.channel = self.get_channel()
        # return self.calc.invoice 

    # def get_calc_cls(self): # override
        # return

    # def invoice_id2profile(self):
        # nama_kelurahan = self.nama_kelurahan()
        # nama_kecamatan = self.nama_kecamatan()
        # nama_propinsi = self.nama_propinsi()
        # self.invoice_profile.from_dict({
            # 'Propinsi': self.invoice_id['Propinsi'],
            # 'Kabupaten': self.invoice_id['Kabupaten'],
            # 'Kecamatan': self.invoice_id['Kecamatan'],
            # 'Kelurahan': self.invoice_id['Kelurahan'],
            # 'Blok': self.invoice_id['Blok'],
            # 'Urut': self.invoice_id['Urut'],
            # 'Jenis': self.invoice_id['Jenis'],
            # 'Tahun Pajak': self.invoice_id['Tahun Pajak'],
            # 'Nama Kelurahan': nama_kelurahan,
            # 'Nama Kecamatan': nama_kecamatan,
            # 'Nama Propinsi': nama_propinsi})

    # def sppt2profile(self): # override
        # pass

    # def set_invoice_profile(self):
        # v = self.invoice_profile.get_raw()
        # self.setBit(62, v) 

    # def _inquiry_response(self):
        # inv = self.get_invoice()
        # if not inv:
            # return
        # if self.calc.paid:
            # return self.ack_already_paid()
        # if self.calc.total <= 0:
            # return self.ack_already_paid_2()
        # settlement_date = self.from_iso.get_settlement()
        # if not settlement_date:
            # return
        # inq = self.create_inquiry()
        # inq.stan = self.from_iso.get_value(11)
        # inq.pengirim = self.from_iso.get_value(33)
        # self.setBit(4, self.calc.total)
        # self.invoice_profile.from_dict({
            # 'Jatuh Tempo': inq.jatuh_tempo.strftime('%Y%m%d'),
            # 'Tagihan': self.calc.tagihan,
            # 'Denda': self.calc.denda,
            # 'Total Bayar': self.calc.total})
        # inq.transmission = self.from_iso.get_transmission()
        # inq.settlement = settlement_date
        # self.set_invoice_profile()
        # DBSession.add(inq)
        # self.commit()

    # def inquiry_response(self):
        # try:
            # self._inquiry_response()
        # except:
            # f = StringIO()
            # traceback.print_exc(file=f)
            # self.log_error(f.getvalue())
            # f.close()
            # self.ack_other('other error')

    # def create_inquiry(self): # override
        # return

    # def _payment_response(self):
        # bank_name = self.conf['name']
        # self.conf.update(host[bank_name])
        # self.copy([4, 48, 62]) # belum di-copy oleh set_transaction_response()
        # self.setBit(47, '') # default payment ID
        # inv = self.get_invoice()
        # if not inv:
            # return
        # invoice_id = self.from_iso.get_value(61).strip()
        # if self.calc.paid:
            # return self.ack_already_paid()
        # if self.calc.total <= 0:
            # return self.ack_already_paid_2()
        # inq = self.invoice2inquiry()
        # if not inq:
            # return self.ack_inquiry_not_found()
        # total_bayar = int(self.from_iso.get_value(4))
        # total_tagihan = self.calc.total
        # if total_bayar != total_tagihan:
            # return self.ack_insufficient_fund(total_bayar, total_tagihan)
        # payment, bayar = self.create_payment(inq, total_bayar)
        # if not payment:
            # return self.ack_create_payment_failed()
        # is_update_sppt and self.calc.set_paid()
        # DBSession.add(inv)
        # DBSession.add(bayar)
        # DBSession.add(payment)
        # self.setBit(47, str(payment.id))
        # self.commit()

    # def payment_response(self):
        # try:
            # self._payment_response()
        # except:
            # f = StringIO()
            # traceback.print_exc(file=f)
            # self.log_error(f.getvalue())
            # f.close()
            # self.ack_other('other error')

    # def invoice2payment(self): # override
        # return

    # def invoice2inquiry(self): # override
        # return

    # def get_channel(self):
        # return self.from_iso.get_value(18) # Merchant / Channel 

    # def get_real_value(self, value):
        # if type(value) is not DictType:
            # return value
        # if self.channel in value:
            # return value[self.channel]
        # if 'default' in value:
            # return value['default']
        # return '00'

    # def bayar(self, inq, total_bayar): # override
        # return

    # def create_payment(self, inq, total_bayar):
        # bayar, urutan_bayar = self.bayar(inq, total_bayar)
        # tp = ''
        # d = bayar.to_dict()
        # for fieldname in self.get_field_bank_non_tp():
            # tp += d[fieldname] or '00'
        # payment_id = create_payment_id(tp)
        # if not payment_id:
            # return None, None
        # payment = Payment(id=payment_id)
        # payment.inquiry_id = inq.id
        # payment.propinsi = inq.propinsi
        # payment.kabupaten = inq.kabupaten
        # payment.kecamatan = inq.kecamatan
        # payment.kelurahan = inq.kelurahan
        # payment.blok = inq.blok
        # payment.urut = inq.urut
        # payment.jenis = inq.jenis
        # payment.tahun = inq.tahun
        # payment.ke = urutan_bayar 
        # for fieldname in self.get_field_bank():
            # value = d[fieldname] or '00'
            # payment.from_dict({fieldname: value})
        # payment.channel = self.channel
        # payment.ntb = self.from_iso.get_value(48) # Nomor Transaksi Bank
        # payment.iso_request = ISO8583.getRawIso(self.from_iso).upper()
        # return payment, bayar

    # def get_field_bank(self): # override
        # return

    # def get_field_bank_non_tp(self): # override
        # return

    # ############
    # # Reversal #
    # ############
    # def _reversal_response(self):
        # reversal_iso_request = ISO8583.getRawIso(self.from_iso).upper()
        # pay_iso_request = '0200' + reversal_iso_request[4:]
        # q = DBSession.query(Payment).filter_by(iso_request=pay_iso_request)
        # pay = q.first()
        # if not pay:
            # return self.ack_payment_not_found()
        # invoice_id = pay2invoice_id(pay)
        # cls = self.get_reversal_cls()
        # rev = cls(pay) 
        # if not rev.bayar:
            # return self.ack_payment_not_found_2(invoice_id, pay.ke)
        # if not rev.invoice:
            # return self.ack_not_available_2(invoice_id)
        # if not rev.is_paid():
            # return self.ack_invoice_open(invoice_id)
        # rev.set_unpaid()
        # reversal = Reversal(payment_id=pay.id) # Catatan tambahan
        # reversal.iso_request = reversal_iso_request
        # DBSession.add(rev.bayar)
        # DBSession.add(rev.invoice)
        # DBSession.add(reversal)
        # self.commit()
        # #self.settlement.set_raw(self.from_iso.get_value(13))

    # def reversal_response(self):
        # try:
            # self._reversal_response()
        # except:
            # f = StringIO()
            # traceback.print_exc(file=f)
            # self.log_error(f.getvalue())
            # f.close()
            # self.ack_other('other error')

    # def get_reversal_cls(self): # override
        # return
 