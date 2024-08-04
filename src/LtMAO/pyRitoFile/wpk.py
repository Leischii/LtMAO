from io import BytesIO
from ..pyRitoFile.io import BinStream


class WPKWem:
    __slots__ = (
        'id', 'offset', 'size'
    )

    def __init__(self):
        self.id = None
        self.offset = None
        self.size = None

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}
    

class WPK:
    __slots__ = ('signature', 'version', 'wems')

    def __init__(self):
        self.signature = None
        self.version = None
        self.wems = None

    def __json__(self):
        return {key: getattr(self, key) for key in self.__slots__}

    def stream(self, path, mode, raw=None):
        if raw != None:
            if raw == True:  # the bool True value
                return BinStream(BytesIO())
            else:
                return BinStream(BytesIO(raw))
        return BinStream(open(path, mode))

    def read(self, path, raw=None):
        with self.stream(path, 'rb', raw) as bs:
            self.signature, = bs.read_a(4)
            if self.signature != 'r3d2':
                raise Exception(
                    f'pyRitoFile: Failed: Read WPK {path}: Wrong signature file: {hex(self.signature)}')
            self.version, = bs.read_u32()
            # read wems offset in wpk
            wem_count, = bs.read_u32()
            self.wems = [WPKWem() for i in range(wem_count)]
            for wem in self.wems:
                wem.offset, = bs.read_u32()
            # remove any wem that has offset 0 
            for wem in self.wems:
                if wem.offset == 0:
                    self.wems.remove(wem)
            wem_count = len(self.wems)
            # now actually read wem info 
            for wem in self.wems:
                bs.seek(wem.offset)
                # update wem.offset as data offset, not wem offset in wpk
                wem.offset, wem.size = bs.read_u32(2)
                wem.id, = bs.read_c_sep_0(bs.read_u32()[0])
                wem.id = int(wem.id.replace('.wem', ''))
            
    def write(self, path, wem_datas, raw=None):
        with self.stream(path, 'wb', raw) as bs:
            # magic, version
            bs.write_a('r3d2')
            bs.write_u32(1)
            # wems offsets - write later
            wem_count = len(self.wems)
            bs.write_u32(wem_count)
            wem_info_offset_start = 9 + wem_count*4
            for wem in self.wems:
                bs.write_u32(wem_info_offset_start)
                wem_info_size = 4+4+4+len(str(wem.id)+'.wem')*2
                wem_info_offset_start+=wem_info_size
            # wem infos
            wem_offsets = []
            for i, wem in enumerate(self.wems):
                wem.size = len(wem_datas[i])
                wem_offsets.append(bs.tell())
                bs.pad(4)
                bs.write_u32(wem.size)
                wem_id = str(wem.id) + '.wem'
                bs.write_u32(len(wem_id)*2)
                bs.write_c_sep_0(wem_id)
            # wem datas
            for i, wem_data in enumerate(wem_datas):
                return_offset = bs.tell()
                bs.seek(wem_offsets[i])
                bs.write(return_offset)
                bs.seek(return_offset, 1)
                bs.write(wem_data)

            return bs.raw() if raw else None 

        
