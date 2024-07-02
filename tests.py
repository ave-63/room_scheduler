import room_scheduler as rs
import csv_importer as ci
# ci.import_schedule("test_schedule_sp_22.csv")

# sections = rs.sections
# prof_list = rs.prof_list

# print(type(sections[0].course))
# print(sections[0].course)
# print(sections[0].prof)
# print(sections[0].time)

# print(prof_list.names)
# print(len(prof_list.names))
# # test_time = room_scheduler.Time(0,1,2,3,"MTWTh")
# test_sect = room_scheduler.Section("123", test_time, "bob")
# test_sect.course
# test_sect.prof
# test_sect.time
# print(sections[-1].prof)
# print(sections[-1].time.start_minute)
# print(sections[-1].time.end_hour)
# print(sections[-1].time.end_minute)
# print(sections[-1].time.days)

# lengths_of_gaps = []
# for g in schedule.gaps:
#     print(g)
#     lengths_of_gaps.append(g.length)
# print(sorted(lengths_of_gaps))

for p in schedules[0].gaps_partition:
    print("Partition:")
    for g in p:
        print(g)



# import itertools as it
# p_sects = [s for s in sections if s.prof == 18]
# p_gaps = []
# for pair in it.combinations(p_sects, 2):
#     g = pair[0].find_gap(pair[1])
#     print(pair[0])
#     print(pair[0].time.session)
#     print(pair[1])
#     print(pair[1].time.session)
#     print(g)
#     print("\n")
#     if g == None:
#         continue
#     else:
#         p_gaps.append(g)

