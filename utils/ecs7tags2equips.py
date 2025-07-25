#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Модуль для поиска и индексирования ECS тегов в проекте
#
import logging
from pathlib import Path
import sqlite3
import time
from exceptions import DirFindError, FileFindError
from alive_progress import alive_bar, config_handler
from colorama import init, Fore
from colorama import Style
import re
import yaml
import csv

# Абсолютный путь к директории c скриптом
_PRG_DIR = Path(__file__).parent.absolute()

_RES_DIR = _PRG_DIR / 'resources'
_TAG_DB_DIR = _RES_DIR / 'FlsaProDb'


_PLCNAME = {0: 'spare', 1: '991', 2: '992', 3: '990'}
_PLCMEMTYP = {
    '17': '16 Bit',
    '21': '16 Bit',
    '22': '32 Bit',
    '23': 'Float',
    '26': '16 Bit/Time',
    '28': 'Float/Stat/Timer',
    '29': '8 Bit',
    '30': 'Flt/Trig/Sts',
}
logger = logging.getLogger()


class DBHelper(object):
    """ECS хранит базу тэгов в формате Ms Access,
    клас работает с конвертированными в sqlite3  файлами mdb ECS.
    """

    def __init__(self):
        self.sdrpoint = _TAG_DB_DIR / 'SdrPoint30.sqlite'
        self.sdrapalg = _TAG_DB_DIR / 'SdrApAlg30.sqlite'
        self.sdrblkalg = _TAG_DB_DIR / 'SdrBlkAlg30.sqlite'
        self.sdrbpalg = _TAG_DB_DIR / 'SdrBpAlg30.sqlite'
        self.sdrsims5config = _TAG_DB_DIR / 'SdrSimS5Config30.sqlite'

        if not self.sdrpoint.is_file() or not self.sdrblkalg.is_file() or not self.sdrbpalg.is_file() \
                or not self.sdrsims5config.is_file():
            raise Exception(f"Can't open db file {self.sdrpoint}")

    @staticmethod
    def _sql_fetchone(bd, sql):
        conn = sqlite3.connect(str(bd))
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result

    def get_blk_alg_name(self, alg_no=0) -> str:
        sql = f"SELECT BlockTableName FROM BlockDescriptionIndex WHERE AlgNo = '{str(alg_no)}'"
        result = self._sql_fetchone(self.sdrblkalg, sql)
        return result[0] if result else f"{alg_no} unknown"

    def get_conv_alg_name(self, alg_no=0) -> str:
        sql = f"SELECT English FROM AlgMaster WHERE CaptionKey = '{str(alg_no)}'"
        result = self._sql_fetchone(self.sdrbpalg, sql)
        return result[0] if result else f"{alg_no} unknown"

    def get_tag(self, tag, only_a_point=False):
        conn = sqlite3.connect(str(self.sdrpoint))
        cursor = conn.cursor()
        # sql = "SELECT PointConfig.PointCode, PointConfig.DefaultText, PointConfig.ConvAlg, PointConfig.CalcAlg," \
        #       "PointConfig.BlockAlg, Groups.GroupCode " \
        #       "FROM PointConfig, Groups " \
        #       f"WHERE PointConfig.PointCode LIKE '%{tag}%' AND Groups.GroupNo = PointConfig.GroupNo;"
        sql = "ATTACH DATABASE ? AS sim"
        # cursor.execute(sql)
        cursor.execute(sql, (str(self.sdrsims5config),))
        sql = f"SELECT *  FROM Points WHERE PointCode LIKE '%{tag}%';"
        sql_apoint = "PointConfig.PointId > 0 AND " if only_a_point is True else ""
        # sql_bpoint = "PointConfig.PointId < 0" if False is True else ""

        sql = "SELECT  PointConfig.PointId, PointConfig.PointCode, PointConfig.DefaultText, PointConfig.LocalText," \
              "ConvAlg, CalcAlg, BlockAlg, " \
              "Groups.GroupCode, sim.Points.PLCNo, " \
              "sim.Points.InputType, InputBlock, InputWord, InputBit, " \
              "sim.Points.OutputType, OutputBlock, OutputWord, OutputBit, ParameterBlock," \
              "PointConfig.BlockAlg, ConvAlg " \
              "FROM PointConfig, Groups, sim.Points " \
              f"WHERE {sql_apoint} PointConfig.PointCode LIKE '%{tag}%' " \
              f"AND PointConfig.PointCode NOT LIKE '%_SPM%' " \
              f"AND PointConfig.PointCode NOT LIKE '%_SPA%' " \
              "AND Groups.GroupNo = PointConfig.GroupNo AND PointConfig.PointId = sim.Points.SDRPointNo;"

        cursor.execute(sql)

        result = cursor.fetchall()

        conn.commit()
        conn.close()
        # return tags
        return result

    # def get_all_tags(self):
    #     conn = sqlite3.connect(str(self.sdrpoint))
    #     cursor = conn.cursor()


class TagsHelper(object):
    def __init__(self, tags_pattern='', with_mimic=False):
        self.db = DBHelper()
        self.tags = []
        self.tags_pattern = tags_pattern
        self.with_mimic = with_mimic
        self.only_a_point = True
        self.only_without_mimic = True
        self.cnt_files = 0  # количество обработаных файлов
        self.cnt_strings = 0  # количество обработаных строк
        self.cnt_tags = 0  # количество обработаных тэгов
        self.index_time = 0
        self.index_date = ""
        self.pages_without_tags = ""
        self.mimic_dir = _RES_DIR / 'ECS2261'
        self.update()
        logger.info(f"Init class TagsHelper")

    def __len__(self):
        return len(self.tags)

    def __getitem__(self, tag):
        for cur_tag in self.tags:
            if cur_tag['Tag'] == tag:
                return cur_tag

    def __iter__(self):
        return iter(self.tags)

    def __get__(self, instance, owner):
        return self.tags

    def update(self):
        """"""
        start_time = time.time()
        self.tags.clear()
        tags = []
        logger.info(f"Start update tags from DB")
        print(f"{Fore.YELLOW}Поиск тегов неиспользуемых на мнемосхемах")
        print(f"{Fore.YELLOW}Выборка из базы. Тег :{Fore.GREEN + self.tags_pattern + Style.RESET_ALL}")
        print(f"{Fore.WHITE}Только A точки: {Fore.GREEN + str(self.only_a_point) + Style.RESET_ALL}")
        print(f"{Fore.WHITE}Без SPA, SPM: {Fore.GREEN + str(True) + Style.RESET_ALL}")
        with alive_bar(1, force_tty=True, length=3) as bar:
            tags = self.db.get_tag(self.tags_pattern, self.only_a_point)
            bar()
        print(f"{Fore.WHITE}Формирования словаря Тегов :{Fore.GREEN + str(len(tags)) + Style.RESET_ALL}")

        for tag in tags:
            tag_data = {
                "Id": tag[0], "Tag": tag[1], "Groups": tag[7], "DescEng": tag[2], "DescRus": str(tag[3]),
                "Tag": tag[1], "Groups": tag[7], "DescEng": tag[2], "DescRus": str(tag[3]),
                "Algorithms": {"ConvAlg": str(tag[4]) + " " + self.db.get_conv_alg_name(tag[4]),
                               "CalcAlg": tag[5],
                               "BlockAlg": str(tag[6]) + " " + self.db.get_blk_alg_name(tag[6])},
                "PLC": {"PLCNo": _PLCNAME.get(tag[8]),
                        # "Input (Type/Block/Word/Bit)": [tag[9], tag[10], tag[11],  tag[12]],
                        "FC": tag[17],
                        "Input": {"Type": _PLCMEMTYP.get(tag[9]),
                                  "Block": tag[10], "Word": tag[11], "Bit": tag[12]},
                        "Output": {"Type": _PLCMEMTYP.get(tag[13]),
                                   "Block": tag[14], "Word": tag[15], "Bit": tag[16]},
                        },
                "PLC_INP": f"%DB{tag[10]}.DBD{tag[11]}",
                "Mimics": '',
            }
            self.tags.append(tag_data)
        if self.with_mimic:
            self.find_tags_on_mimics()

        self.index_time = time.time() - start_time
        print(f"{Fore.WHITE}Обработано файлов: {Fore.GREEN + str(self.cnt_files) + Style.RESET_ALL}")
        print(f"{Fore.WHITE}За время: {Fore.GREEN + str(self.index_time) + Style.RESET_ALL}")
        logger.info(f"Update complite")

    def find_tags_on_mimics(self):
        """"""
        i = 0
        self.cnt_files = 0
        mimics_in_dir = self.mimic_dir.glob('*.g')
        mimics_col = sum([1 for _ in self.mimic_dir.glob('*.g')])
        print(f"{Fore.YELLOW}Поиск тегов на мнемосхемах\r\n"
              # f"{Fore.YELLOW}Опции: \r\n"
              #   f"   {Fore.WHITE}Только А точки = {Fore.GREEN}{self.only_a_point} \r\n"
              #   f"   {Fore.WHITE}Только теги бех мнемосхема = {Fore.GREEN}{self.only_without_mimic}{Fore.WHITE} \r\n"
              f"{Fore.WHITE}Количество тегов: {Fore.GREEN} {len(self.tags)}{Fore.WHITE}\r\n"
              f"{Fore.WHITE}Количество мнемосхем: {Fore.GREEN} {mimics_col}{Fore.WHITE}")

        with alive_bar(len(self.tags), force_tty=True, length=30) as bar:
            for tag in self.tags:
                mimics_list = []
                for mimic in self.mimic_dir.glob('*.g'):
                    if self.find_tag_on_mimic(mimic, tag['Tag']):
                        mimics_list.append(mimic.name)
                    self.cnt_files += 1

                self.tags[i]['Mimics'] = mimics_list
                i += 1
                bar()

    def find_tag_on_mimic(self, mimic, tag) -> bool:
        """"""
        mim = _RES_DIR / 'ECS2261' / mimic
        if not mim.is_file():
            err_msg = f"Cannot find file: {mim} "
            logger.error(err_msg)
            raise FileFindError(err_msg)
        else:
            with open(mim) as f:
                if tag in f.read():
                    return True

    def get_tags_without_mimic(self) -> list:
        """"""
        tag_wo_mim = []
        for tag in self.tags:
            if len(tag['Mimics']) == 0:
                tag_wo_mim.append(tag)

        print(f"{Fore.WHITE}Тегов без мнемомосхем:{Fore.GREEN}  {len(tag_wo_mim)}  {Style.RESET_ALL}")
        return tag_wo_mim

    @staticmethod
    def to_yaml(tags) -> str:
        return yaml.dump(tags, default_flow_style=False, indent=3, sort_keys=False, allow_unicode=True)

    def save_csv(self, tags=None):
        """"""
        tags = tags or self.tags
        field_names = ['Id', 'Tag', 'DescEng', 'DescRus', 'Groups', 'PLC', 'PLC_INP', 'Algorithms', 'Mimics']
        with open('tags.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names, )
            writer.writeheader()
            writer.writerows(tags)
        print(f"{Fore.YELLOW}Теги сохранены в:{Fore.GREEN}  tags.csv  {Style.RESET_ALL}")

    def save_yaml(self, tags=None):
        """"""
        tags = tags or self.tags
        tags = self.to_yaml(tags)
        with open("tags.yaml", 'w') as target:
            target.write(tags)
        print(f"{Fore.YELLOW}Теги сохранены в :{Fore.GREEN}  tags.yaml   {Style.RESET_ALL}")

    def save_telegraf(self, tags=None):
        """Перечень OPC тегов для telegraf.conf"""
        tags = tags or self.tags
        field_names = ['Id', 'Tag', 'DescEng', 'DescRus', 'Groups', 'PLC', 'PLC_INP', 'Algorithms', 'Mimics']
        nodes =[]
        tags_str = "   nodes = [\n"
        with open('tags.telegraf.conf', 'w', newline='') as tconf:
            for tag in tags:
                tags_str += (f'     {{name="{tag["Tag"]} {tag["DescEng"]}", namespace="1", identifier_type="s", '
                             f'identifier="t|{tag["Tag"]}"}},\n')

            tags_str += "]"
            tconf.write(tags_str)

        print(f"{Fore.YELLOW}Теги сохранены в:{Fore.GREEN}  tags.csv  {Style.RESET_ALL}")

    def save_equip_json(self, tags=None):
        """Сохраняет теги в формате equips.json"""
        import json
        tags = tags or self.tags
        equips = []
        for tag in tags:
            eq_name = tag["Tag"].replace("", "")
            equip = {
                "eq_name": eq_name,
                "plc_name": tag["PLC"]["PLCNo"],
                "db_num": tag["PLC"]["Input"]["Block"],
                "db_addr": int(tag["PLC"]["Input"]["Word"] or 0) + 16
            }
            equips.append(equip)
        data = {"equips": equips}
        with open("equips.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"{Fore.YELLOW}Оборудование сохранено в: {Fore.GREEN}  equips.json  {Style.RESET_ALL}")


def main():
    tags = TagsHelper("MAINT%_MH", with_mimic=False)
    # tags_wi_mim = tags.get_tags_without_mimic()
    # tags.save_csv()
    # tags.save_telegraf()
    tags.save_equip_json()

if __name__ == '__main__':
    main()
