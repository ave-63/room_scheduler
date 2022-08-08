from __future__ import annotations  # solves problem of annotating self return values
import itertools as it
# import csv_importer as ci
import copy
import random
import csv
import re

# TODO: figure out how to make 4-day/week gaps twice as important as 2-day/week gaps
# TODO: figure out how to recognize online classes from csv

# TODO: figure out how to recognize online classes from csv

def import_schedule(csv_file):
    # populates sections and prof_list; returns (sections, prof_list)
    sections = []
    prof_list = Prof_List()
    with open(csv_file, newline = '') as input_file:
        reader = iter(csv.DictReader(input_file, delimiter=','))
        for row in reader:
            if row["Section"] == "":
                print("skipping empty row")
                continue
            start_time_match = re.search("(\d+):(\d+)", row["Start"])
            if start_time_match:
                start_time_str = start_time_match.groups()
                start_time_hr = int(start_time_str[0])
                start_time_min = int(start_time_str[1])
            else:
                raise Exception("Unclear start time in csv: {}".format(row["Start"]))
            if re.search("PM$", row["Start"]) and start_time_hr != 12:
                start_time_hr += 12  # add 12 hours if PM
            end_time_match = re.search("(\d+):(\d+)", row["End"])
            if end_time_match:
                end_time_str = end_time_match.groups()
                end_time_hr = int(end_time_str[0])
                end_time_min = int(end_time_str[1])
                if re.search("PM$", row["End"]) and end_time_hr != 12:
                    end_time_hr += 12  # add 12 hours if PM
            else:
                raise Exception("Unclear end time in csv: {}".format(row["End"]))
            prof_name = ", ".join([row["Name"], row["Init"]])
            # print(prof_list.names, prof_name)
            prof_list.add_name(prof_name)
            prof_index = prof_list.get_id(prof_name)
            time = Time(start_time_hr, start_time_min, end_time_hr, end_time_min,
                                       row["Days"], row["Session"])
            # WARNING: this probably needs checking by hand
            if "Online" in row:
                online = row["Online"] not in ["no", "No", "NO", ""] or\
                         row["Room"] in ["ONLINE", "Online" "SYNCHRONOUS", ""]
            else:
                # assume blank room means class is online.
                online = row["Room"] in ["ONLINE", "SYNCHRONOUS", ""]
            sections.append(Section(row["Course"], time, prof_index, online))
    return (sections, prof_list)


class Time:
    def __init__(self, start_hour: int, start_minute: int,
                 end_hour: int, end_minute: int, days: str, session: str):
        # input: start_hour, end_hour, between 0 and 23
        # input: start_minute, end_minute between 0 and 59
        # data: start, end are number of minutes after midnight!
        # days: "MW" "TTh" or "MTWTh"
        # session: "A" "B" or "AB"
        self.start = start_hour*60 + start_minute
        self.end = end_hour*60 + end_minute
        match session:
            case "A":
                self.session = 0
            case "B":
                self.session = 1
            case "AB":
                self.session = 2
            case _:
                raise Exception("Bad session code, neither A, B, nor AB: {}".format(session))
        match days:
            case "MW":
                self.days = 0
            case "TTh":
                self.days = 1
            case "MTWTh":
                self.days = 2
            case _:
                raise Exception("Bad day of week, neither MW, TTh, nor MTWTh: {}".format(days))

    def __repr__(self):
        start_hour = int(self.start/60)
        start_minute = self.start % 60
        end_hour = int(self.end/60)
        end_minute = self.end % 60
        days = "undefinded days"
        match self.session:
            case 0:
                session = "A"
            case 1:
                session = "B"
            case 2:
                session = "AB"
        match self.days:
            case 0:
                days = "MW"
            case 1:
                days = "TTh"
            case 2:
                days = "MTWTh"
        return "{}:{} to {}:{} on {}, session {}"\
          .format(start_hour,start_minute,end_hour,end_minute,days,session)

class Section:
    # time is Time object, created beforehand
    # course is string, eg "228A" or "261"
    # prof is index in the Prof_List
    # online is bool
    def __init__(self, course: str, time: Time, prof: int, online: bool):
        self.course = course
        self.time = time
        self.prof = prof
        self.online = online

    def overlaps_p(self, other: Section) -> bool:
        # True iff self and other overlap
        if self.time.days + other.time.days == 1:
            # MW and TTh or vice versa
            return False
        if self.time.session + other.time.session == 1:
            # Session A and B or vice versa
            return False
        if self.time.start > other.time.end:
            return False
        if self.time.end < other.time.start:
            return False
        return True

    def find_gap(self, other: Section) -> None | Gap:
        # return None if self, other are on different days, or both are online
        #   or if gap_length > max_gap
        # otherwise return a Gap object
        if self.online and other.online:
            return None
        if self.time.days == 0 and other.time.days == 1:
            return None
        if self.time.days == 1 and other.time.days == 0:
            return None
        if self.time.session == 0 and other.time.session == 1:
            return None
        if self.time.session == 1 and other.time.session == 0:
            return None
        if self.time.start < other.time.end:
            first = self
            second = other
        else:
            first = other
            second = self
        if first.time.end > second.time.start:
            raise Exception("Can't find gap between overlapping classes: " + \
                            str(first) + " and " + str(second))
        gap_length = second.time.start - first.time.end
        if gap_length > gap_max:
            return None
        return Gap(second.time.start - first.time.end, first, second)
    
    def __repr__(self):
        time_str = str(self.time)
        prof_name = prof_list.names[self.prof]
        return "Math {}, {}, {}".format(self.course, time_str, prof_name)


class Gap:
    # int length (minutes)
    # Section first
    # Section second
    def __init__(self, length: int, first: Section, second: Section):
        self.length = length
        self.first = first
        self.second = second
        self.half_online = first.online or second.online
        
    def __repr__(self):
        return "First section:" +\
        prof_list.names[self.first.prof] + " " + self.first.course +\
        " " + str(self.first.time) + "\n" +\
        "Second section:" +\
        prof_list.names[self.second.prof] + " "+ self.second.course +" "+ str(self.second.time) + "\n"


class Prof_List:
    # list of names (strings), index is ID
    # list of lists of unwanted rooms
    # singleton; should only be changed by csv_importer
    def __init__(self):
        self.names = []
        self.bad_rooms = []
        self.avoid_bad_rooms_by_splitting_gaps = []

    def add_name(self, name: str):
        if name not in self.names:
            self.names.append(name)
            self.bad_rooms.append([])
            self.avoid_bad_rooms_by_splitting_gaps.append(True)

    def get_id(self, name: str) -> int:
        return self.names.index(name)

    def set_bad_rooms(self, name: str, bad_rooms: list):
        # alternative to my_prof_list.bad_rooms[index] = bad_rooms
        index = self.names.index(name)
        self.bad_rooms[index] = bad_rooms

    def get_bad_rooms(self, name: str) -> list:
        # alternative to my_prof_list.bad_rooms[index]
        index = self.names.index(name)
        return self.bad_rooms[index]


# idea: no data structure for prof needed during big algorithm.
# instead, put relevant stuff straight in Schedule. Keep Prof for input/output
# and for preparing data for big algorithm.



class Schedule:
    # rooms: dict of schedule: keys are rooms (int), values are lists of sections
    # unroomed_sects: list of unroomed Sections
    # gaps: list of unroomed gaps, where one (or both?) sections are unroomed
    # gaps_partition: list of lists of gaps. Each list has sections for one prof that
    #                 are all connected, hopefully to be scheduled in same room
    # int score = sum, over all gaps, of 1/(minutes between classes NOT in same room)
    #             + 1/60*(#online classes not in same room as nearby in-person class)
    # plan: use copy.deepcopy() to make alt schedules with changes.
    # TODO: remember that "STAFF" is really many people and we should ignore their gaps.
    #       We still need to assign STAFF rooms though.
    def __init__(self, sects):
        # initialize a starting schedule; all sects start unroomed
        # and find gaps, initialize score
        self.unroomed_sects = copy.copy(sects)
        self.rooms = {}
        self.sects_in_bad_rooms = [] # one measure of how bad a finished schedule is
        self.split_in_person_gaps = []  # one measure of how bad a finished schedule is
        # sections that were part of a gap that were kicked out of the room the gap was in.
        self.online_sects_kicked = [] 
        room_nums = projectors.keys()
        for n in room_nums:
            self.rooms[n] = []
        self.gaps = []
        self.gaps_partition = []
        self.score = 0  # no split gaps yet
        # next, populate gaps list:
        for p in range(len(prof_list.names)):
            # get list of sections for p
            if prof_list.names[p][0:5] == "STAFF":
                continue
            p_sects = [s for s in sects if p == s.prof]
            p_gaps = []
            for pair in it.combinations(p_sects, 2):
                g = pair[0].find_gap(pair[1])
                if g == None:
                    continue
                else:
                    p_gaps.append(g)
            for s in p_sects:
                # list all gaps where s is first
                s_first_gaps = [g for g in p_gaps if g.first == s]
                # count only the shortest gap after s;
                # others are later in the day and should be removed
                if s_first_gaps != []:
                    shortest = min(s_first_gaps, key = lambda g: g.length)
                    for g in s_first_gaps:
                        g_second_days_subset_of_sh_second_days =\
                          (shortest.second.time.days == g.second.time.days or\
                          shortest.second.time.days == 2) and\
                          shortest.second.time.session + g.second.time.session != 1
                          # This feels hacky and I'm not sure it's always corect...
                        if g != shortest and g_second_days_subset_of_sh_second_days:
                            p_gaps.remove(g)
            self.gaps.extend(p_gaps)
        for g in self.gaps:
            done_with_g = False
            for p in self.gaps_partition:
                for f in p:
                    if f.first == g.second or f.second == g.first or\
                       f.first == g.first or f.second == g.second:
                        p.append(g)
                        done_with_g = True
                        break
                if done_with_g:
                    break
            if not done_with_g:
                # g didn't fit among any partitions p so create a new partition
                self.gaps_partition.append([g])
        # now check to see if any partitions need to be merged
        for p, q in it.combinations(self.gaps_partition, 2):
            for pg, qg in it.product(p,q):
                #for every pair of gaps pg, qg with pg in p and qg in q:
                if pg.first == qg.second or pg.second == qg.first or\
                   pg.first == qg.first or pg.second == qg.second:
                    # make p the union of p and q
                    p.extend(q)
                    self.gaps_partition.remove(q)
            

    def fits_in_room_p(self, sect: Section, room: int) -> bool | list:
        # Returns True iff sect doesn't overlap with ANY sections in room.
        # Returns False iff sect overlaps with in-person sections in room.
        # Returns list of Sects iff sect overplaps with online section(s) in room.
        overlapping = []
        for s in self.rooms[room]:
            if sect.overlaps_p(s):
                if s.online:
                    overlapping.append(s)
                else:
                    return False # sect overlaps with in-person s
        if overlapping == []:
            return True
        else:
            return overlapping

    # def put_gaps_in_a_room(self, gaps: list) -> bool:
    #     # old version
    #     # Attempts to put all classes from gaps in one room.
    #     # gaps must be list of gaps, all for one prof.
    #     # returns True if possible, false if not.
    #     # If successful, self.rooms, self.gaps, self.unroomed_sects are updated.
    #     if gaps == []:
    #         raise Exception("gaps is empty, ya dingus.")
    #     g_sects = [g.first for g in gaps] + [g.second for g in gaps]
    #     g_sects = list(set(g_sects))
    #     # g_sects now has all sections from gaps with no duplicates
    #     prof = gaps[0].first.prof
    #     ok_rooms = [r for r in self.rooms.keys() if r not in prof_list.bad_rooms[prof]]
    #     random.shuffle(ok_rooms)  # try rooms in random order for extra randomness
    #     for r in ok_rooms:
    #         g_sects_fit_in_r = True
    #         for s in g_sects:
    #             if not self.fits_in_room_p(s, r):
    #                 g_sects_fit_in_r = False
    #                 break
    #         if g_sects_fit_in_r:
    #             self.rooms[r].extend(g_sects)
    #             for s in g_sects:
    #                 if s in self.unroomed_sects:
    #                     self.unroomed_sects.remove(s)
    #             for g in gaps:
    #                 self.gaps.remove(g)
    #             return True
    #     # No room in ok_rooms, so let's try bad rooms.
    #     if not prof_list.avoid_bad_rooms_by_splitting_gaps[prof]:
    #         for r in prof_list.bad_rooms[prof]:
    #             g_sects_fit_in_r = True
    #             for s in g_sects:
    #                 if not self.fits_in_room_p(s, r):
    #                     g_sects_fit_in_r = False
    #                     break
    #             if g_sects_fit_in_r:
    #                 self.rooms[r].extend(g_sects)
    #                 for s in g_sects:
    #                     if s in self.unroomed_sects:
    #                         self.unroomed_sects.remove(s)
    #                 for g in gaps:
    #                     self.gaps.remove(g)
    #                 return True
    #     # If we got here without returning True, g_sects don't fit in any room
    #     return False

    # def sub_put_gaps_in_a_room(self, gaps: list, bad_rooms_ok: bool,
    #                            kick_online_ok: bool, split_gaps_ok: bool) -> bool:
    # OLD VERSION TO DELETE
    #     # only to be called by put_gaps_in_a_room()
    #     # True if successfully completed, otherwise False and nothing is changed.
    #     # bad_rooms_ok should be True ONLY if you already tried with bad_rooms_ok = False.
    #     # This function will will not prioritize good rooms when bad_rooms_ok = True.
    #     if gaps == []:
    #         raise Exception("gaps is empty, ya dingus.")
    #     g_sects = [g.first for g in gaps] + [g.second for g in gaps]
    #     g_sects = list(set(g_sects))
    #     # g_sects now has all sections from gaps with no duplicates
    #     prof = gaps[0].first.prof
    #     ok_rooms = [r for r in self.rooms.keys() if r not in prof_list.bad_rooms[prof]]
    #     if bad_rooms_ok:
    #         ok_rooms = list(self.rooms.keys())
    #     random.shuffle(ok_rooms)  # try rooms in random order for extra randomness
    #     g_sects_that_dont_fit = {} # keys:rooms. Entries are sections in gaps that don't fit in room 
    #     online_sects_to_kick = {}  # keys:rooms. Entries are online sections in room that must be kicked
    #     for n in ok_rooms:
    #         g_sects_that_dont_fit[n] = []
    #         online_sects_to_kick[n] = []
    #     for r in ok_rooms:
    #         for s in g_sects:
    #             s_fits_in_r = self.fits_in_room_p(s, r)
    #             if s_fits_in_r == False:
    #                 g_sects_that_dont_fit[r].append(s)
    #             if not kick_online_ok and type(s_fits_in_r) == type([]):
    #                 g_sects_that_dont_fit[r].append(s)
    #             if kick_online_ok and type(s_fits_in_r) == type([]):
    #                 online_sects_to_kick[r].extend(s_fits_in_r)
    #     # if both kick_online_ok and split_gaps_ok, prioritize no_split_gaps.
    #     # make list (lsdf) of room numbers tied for least number of sects that don't fit
    #     # find the chosen_r in lsdf such that online_sects_to_kick[chosen_r] is minimized.
    #     min_len = min([len(sdf) for sdf in g_sects_that_dont_fit.values()])
    #     # min_len is the smallest number of sections that don't fit for all rooms
    #     lsdf = [r for r in g_sects_that_dont_fit.keys() if len(g_sects_that_dont_fit[r]) == min_len]
    #     # lsdf is list of rooms tied for least number of sects in gaps that don't fit
    #     chosen_r = lsdf[0]
    #     for r in lsdf:
    #         if len(online_sects_to_kick[r]) < len(online_sects_to_kick[chosen_r]):
    #             chosen_r = r
    #     # At this point, chosen_r is one of the rooms with the least number of sections in
    #     # g_sects that don't fit. When two rooms are tied for the least number of sects that
    #     # don't fit, chosen_r is one of the rooms with least online_sects_to_kick.
    #     # Most of the time, min_len == 0, and len(online_sects_to_kick[chosen_r] == 0.
    #     if not split_gaps_ok and len(g_sects_that_dont_fit[chosen_r]) != 0:
    #         return 
    def put_gaps_in_a_room(self, gaps: list):
        if gaps == []:
            raise Exception("gaps is empty, ya dingus.")
        prof = gaps[0].first.prof
        if self.sub_put_gaps_in_a_room(gaps, bad_rooms_ok = False, split_gaps_ok = False):
            return
        if prof_list.avoid_bad_rooms_by_splitting_gaps[prof]:
            self.sub_put_gaps_in_a_room(gaps, bad_rooms_ok = False, split_gaps_ok = True)
            # It should always be successful with split_gaps_ok so ...
            return
        else:
            if self.sub_put_gaps_in_a_room(gaps, bad_rooms_ok = True, split_gaps_ok = False):
                return
            elif self.sub_put_gaps_in_a_room(gaps, bad_rooms_ok = False, split_gaps_ok = True):
                return
        # At this point, we've tried split_gaps_ok = True which is always successful
        return
        
        
    def sub_put_gaps_in_a_room(self, gaps: list, bad_rooms_ok: bool,
                               split_gaps_ok: bool) -> bool:
        # True if successfully completed, otherwise False and nothing is changed.
        # bad_rooms_ok should False; only True when calling recursively.
        # This function will will not prioritize good rooms when bad_rooms_ok = True.
        if gaps == []:
            raise Exception("gaps is empty, ya dingus.")
        g_sects = [g.first for g in gaps] + [g.second for g in gaps]
        g_sects = list(set(g_sects))
        # g_sects now has all sections from gaps with no duplicates
        prof = gaps[0].first.prof
        ok_rooms = [r for r in self.rooms.keys() if r not in prof_list.bad_rooms[prof]]
        if bad_rooms_ok:
            ok_rooms = list(self.rooms.keys())
        random.shuffle(ok_rooms)  # try rooms in random order for extra randomness
        g_sects_that_dont_fit = {} # keys:rooms. Entries are sections in gaps that don't fit in room 
        online_sects_to_kick = {}  # keys:rooms. Entries are online sections in room that must be kicked
        for n in ok_rooms:
            g_sects_that_dont_fit[n] = []
            online_sects_to_kick[n] = []
        for r in ok_rooms:
            for s in g_sects:
                s_fits_in_r = self.fits_in_room_p(s, r)
                if s_fits_in_r == False:
                    g_sects_that_dont_fit[r].append(s)
                if type(s_fits_in_r) == type([]):
                    online_sects_to_kick[r].extend(s_fits_in_r)
        # if both kick_online_ok and split_gaps_ok, prioritize no_split_gaps.
        # make list (lsdf) of room numbers tied for least number of sects that don't fit
        # find the chosen_r in lsdf such that online_sects_to_kick[chosen_r] is minimized.
        min_len = min([len(sdf) for sdf in g_sects_that_dont_fit.values()])
        # min_len is the smallest number of sections that don't fit for all rooms
        lsdf = [r for r in g_sects_that_dont_fit.keys() if len(g_sects_that_dont_fit[r]) == min_len]
        # lsdf is list of rooms tied for least number of sects in gaps that don't fit
        chosen_r = lsdf[0]
        for r in lsdf:
            if len(online_sects_to_kick[r]) < len(online_sects_to_kick[chosen_r]):
                chosen_r = r
        # At this point, chosen_r is one of the rooms with the least number of sections in
        # g_sects that don't fit. When two rooms are tied for the least number of sects that
        # don't fit, chosen_r is one of the rooms with least online_sects_to_kick.
        # Most of the time, min_len == 0, and len(online_sects_to_kick[chosen_r] == 0.
        if not split_gaps_ok and len(g_sects_that_dont_fit[chosen_r]) != 0:
            return False
        for s in online_sects_to_kick:
            self.online_sects_kicked.append(s)
            self.rooms[chosen_r].remove(s)
            self.unroomed_sects.append(s)
        for s in g_sects_that_dont_fit:
            split_gaps = []
            for g in gaps:
                if (s == g.first or s == g.second) \
                  and not g.first.online and not g.second.online:
                    self.split_in_person_gaps.append(s)
        for s in g_sects:
            if s not in g_sects_that_dont_fit:
                self.rooms[chosen_r].append(s)
                self.unroomed_sects.remove(s)
        return True
            

            
        #     if g_sects_that_dont_fit_in_r == []:
        #         # r has room for all of g_sects
        #         for os in online_sects_to_kick:
        #             self.rooms[r].remove(os)
        #             self.online_sects_kicked.append(os)
        #         self.rooms[r].extend(g_sects)
        #         for s in g_sects:
        #             if s in self.unroomed_sects:
        #                 self.unroomed_sects.remove(s)
        #         for g in gaps:
        #             self.gaps.remove(g)
        #         return True
        # # If we got here without returning True, g_sects don't fit in any room
        # return False
        
    # def put_gaps_in_a_room(self, gaps: list) -> bool:
    #     # new version
    #     # Attempts to put all classes from gaps in one room.
    #     # gaps must be list of gaps, all for one prof.
    #     # returns True if possible, false if not.
    #     # If successful, self.rooms, self.gaps, self.unroomed_sects are updated.
    #     if gaps == []:
    #         raise Exception("gaps is empty, ya dingus.")
    #     g_sects = [g.first for g in gaps] + [g.second for g in gaps]
    #     g_sects = list(set(g_sects))
    #     # g_sects now has all sections from gaps with no duplicates
    #     prof = gaps[0].first.prof
    #     ok_rooms = [r for r in self.rooms.keys() if r not in prof_list.bad_rooms[prof]]
    #     random.shuffle(ok_rooms)  # try rooms in random order for extra randomness
    #     for r in ok_rooms:
    #         g_sects_fit_in_r = True
    #         for s in g_sects:
    #             if not self.fits_in_room_p(s, r):
    #                 g_sects_fit_in_r = False
    #                 break
    #         if g_sects_fit_in_r:
    #             self.rooms[r].extend(g_sects)
    #             for s in g_sects:
    #                 if s in self.unroomed_sects:
    #                     self.unroomed_sects.remove(s)
    #             for g in gaps:
    #                 self.gaps.remove(g)
    #             return True
    #     # No room in ok_rooms, so let's try bad rooms.
    #     if not prof_list.avoid_bad_rooms_by_splitting_gaps[prof]:
    #         for r in prof_list.bad_rooms[prof]:
    #             g_sects_fit_in_r = True
    #             for s in g_sects:
    #                 if not self.fits_in_room_p(s, r):
    #                     g_sects_fit_in_r = False
    #                     break
    #             if g_sects_fit_in_r:
    #                 self.rooms[r].extend(g_sects)
    #                 for s in g_sects:
    #                     if s in self.unroomed_sects:
    #                         self.unroomed_sects.remove(s)
    #                 for g in gaps:
    #                     self.gaps.remove(g)
    #                 return True
    #     # If we got here without returning True, g_sects don't fit in any room
    #     return False
    def put_sect_in_a_room(self, sect: Section) -> bool:
        # Attempts to put sect, which must be in unroomed_sects, in some room.
        # Returns false if this is not possible (which shouldn't happen)
        if sect not in self.unroomed_sects:
            raise Exception("Section {} is not in unroomed_sects.")
        prof = sect.prof
        ok_rooms = [r for r in self.rooms.keys() if r not in prof_list.bad_rooms[prof]]
        random.shuffle(ok_rooms)
        # TODO: move room that prof is already in to front of list?
        for r in ok_rooms:
            if self.fits_in_room_p(sect, r):
                self.rooms[r].append(sect)
                self.unroomed_sects.remove(sect)
                return True
        for r in prof_list.bad_rooms[prof]:
            if self.fits_in_room_p(sect, r):
                self.rooms[r].append(sect)
                self.unroomed_sects.remove(sect)
                self.sects_in_bad_rooms.append(sect)
                return True
        return False
    
    def sort_rooms(self):
        # put each list in rooms in chronological order
        for k in self.rooms.keys():
            self.rooms[k].sort(key = lambda s: s.time.start)
        
    def __repr__(self):
        self.sort_rooms()
        output = ""
        keys = self.rooms.keys()
        for k in keys:
            output += "In room " + str(k) + ":\n"
            for s in self.rooms[k]:
                output += str(s) + "\n"
        output += "Unassigned Sections: \n"
        for s in self.unroomed_sects:
            output += str(s) + "\n"
        return output
        
    # TODO: def put_sect_in_a_room(self, sect: Section) -> bool
    # TODO: def export_to_csv(self, file_name: str):
    # TODO: figure out how to avoid splitting half-online gaps
    # TODO: professor preferences!
        


# create the singletons sections, prof_list, filled by csv_importer
sections, prof_list = import_schedule("test_schedule_sp_22.csv")
gap_max = 60 # don't consider longer gaps, to encourage OH in CAS.
closest = {1003: [1203, 1204, 1205, 1206, 1107, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1107:[1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],

           1203: [1204, 1205, 1206, 1107, 1003, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1204:[1003, 1203, 1205, 1206, 1107, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1205:[1003, 1203, 1204, 1206, 1107, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1206:[1203, 1204, 1205, 1107, 1310, 1003, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1310:[1203, 1204, 1205, 1206, 1107, 1003, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1400:[1310, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1003, 1107, 1203, 1204, 1205, 1206, 1512, 8101], # TODO: Finish this, after looking at map
           1401:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1402:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1403, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1403:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1412, 1413, 1414, 1415, 1416, 1512, 8101],
           1412:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1413, 1414, 1415, 1416, 1512, 8101],
           1413:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1414, 1415, 1416, 1512, 8101],
           1414:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1415, 1416, 1512, 8101],
           1415:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1416, 1512, 8101],
           1416:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1512, 8101],
           1512:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 8101],
           8101:[1003, 1107, 1203, 1204, 1205, 1206, 1310, 1400, 1401, 1402, 1403, 1412, 1413, 1414, 1415, 1416, 1512]}
projectors = {1003:2,
              1107:1, # 1107 has not been checked
              1203:1,
              1204:1,
              1205:1,
              1206:1,
              1310:1,
              1400:2,
              1401:2,
              1402:2,
              1403:2,
              1412:2,
              1413:1,
              1414:1,
              1415:1,
              1416:1,
              1512:2,
              8101:1} # 8101 has not been checked!
num_attempts = 50
schedules = [Schedule(sections) for i in range(num_attempts)]
gap_set_order = list(range(len(schedules[0].gaps_partition)))
print(schedules[0].gaps)
failures = [False for i in range(num_attempts)]
for i in range(len(schedules)):
    random.shuffle(gap_set_order)
    for s in gap_set_order:
        success = schedules[i].put_gaps_in_a_room(schedules[i].gaps_partition[s])
        if not success:
            failures[i] = True
            print("In iteration ", i)
            print("Could not find room for gap set:", s)
            print(schedules[i].gaps_partition[s])
    random.shuffle(schedules[i].unroomed_sects)
    for s in schedules[i].unroomed_sects:
        if not schedules[i].put_sect_in_a_room(s):
            print("OH NO! Could not find a room for {} in iteration {}".format(s,i))

successes = [i for i in range(len(failures)) if failures[i]==False]
print(successes)

