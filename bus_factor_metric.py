__author__ = 'atlanmod'

from datetime import datetime
import simplejson as json
import codecs
import re

class Metrics():

    DEFAULT = "default"

    def __init__(self, json_repo_path, json_bus_factor_dir, bus_factor_calculation,
                 primary_expert_knowledge,
                 secondary_expert_knowledge_proportion, logger):
        self.logger = logger
        self.JSON_REPO_PATH = json_repo_path
        self.JSON_BUS_FACTOR_DIR = json_bus_factor_dir

        self.USERS = set()
        self.TOTAL_FILES = 0
        self.EXTENSIONS = {}

        #last_change
        #multiple_changes
        #distinct_changes
        #weighted_distinct_changes
        self.DEVELOPER_KNOWLEDGE_CALCULATION = bus_factor_calculation

        if primary_expert_knowledge != self.DEFAULT:
            self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION = primary_expert_knowledge
        else:
            self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION = self.DEFAULT

        if secondary_expert_knowledge_proportion == self.DEFAULT:
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = 0.5
        else:
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = secondary_expert_knowledge_proportion

    def get_sorted_keys(self, dictionary):
        return sorted(dictionary, key=dictionary.get, reverse=True)

    def get_developer_knowledge_percentage(self, authors2changes):
        number_of_changes = sum(authors2changes.values())

        developer_knowledge_percentage = {}
        for k in authors2changes.keys():
            percentage_author_changes = round((authors2changes.get(k)/float(number_of_changes))*100, 2)
            developer_knowledge_percentage.update({k: percentage_author_changes})

        return developer_knowledge_percentage

    #get the authors that made more modifications on a part of code (ex.: line, file)
    #A primary expert is an author that has modified more than 1/N percentage of the file, where N is the number of authors that modified the file
    def get_primary_experts(self, authors2changes):
        primary_experts = []
        developers_knowledge_percentage = self.get_developer_knowledge_percentage(authors2changes)
        developers_knowledge_percentage_sorted_keys = self.get_sorted_keys(developers_knowledge_percentage)

        number_of_authors = len(authors2changes.keys())

        if self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION == self.DEFAULT:
            primary_expert_proportion = 1/float(number_of_authors)
        else:
            primary_expert_proportion = self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION

        primary_expertise_threshold = round(primary_expert_proportion*100, 2)

        for k in developers_knowledge_percentage_sorted_keys:
            if developers_knowledge_percentage.get(k) >= primary_expertise_threshold:
                primary_experts.append((k, developers_knowledge_percentage.get(k)))
            else:
                break

        return primary_experts

    #get the bus factor for a file
    #The bus factor is calculate according to the primary experts of the files plus the authors that hold at least half of the knowledge of the primary experts
    #If there are more than one primary experts, the bus factor will include the authors that have more than the average of the primary experts' percentage
    #Ex.: if the primary experts own 60% of the file, an author to be considered a secondary expert part of the bus factor should hold at least the 30% of the files
    def get_bus_factor_authors(self, authors2changes):
        experts_in_bus_factor = []
        developer_knowledge_percentage = self.get_developer_knowledge_percentage(authors2changes)
        developer_knowledge_percentage_sorted_keys = self.get_sorted_keys(developer_knowledge_percentage)

        primary_experts = self.get_primary_experts(authors2changes)

        primary_expertise_percentage_value = 0
        for pe in primary_experts:
            primary_expertise_percentage_value = primary_expertise_percentage_value + pe[1]

        bus_factor_threshold = round((primary_expertise_percentage_value/len(primary_experts))*self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION, 2)

        for k in developer_knowledge_percentage_sorted_keys:
            if developer_knowledge_percentage.get(k) >= bus_factor_threshold:
                experts_in_bus_factor.append((k, developer_knowledge_percentage.get(k)))
            else:
                break

        return experts_in_bus_factor

    #calculate the developer knowledge of a line according to the position of the change in the history of the line
    #Ex.: A, B, D are 3 users: A -> B -> A -> B -> B -> D is converted to A -> B -> A -> B -> D and then
    # A x 1 -> B x 2 -> A x 3 -> B x 4 -> D x 5 so then A = 4, B = 6, D = 5
    def calculate_developer_knowledge_line_weighted_distinct_changes(self, line):
        #collect the number of changes per author for the line
        line_authors2changes = {}
        changes = line.get('line_changes')
        changes.reverse()
        previous_author = ""
        authors = []
        #collect the authors
        for change in changes:
            author = change.get('author').get('name')
            if author != previous_author:
                authors.append(author)
                previous_author = author

        pos = 1
        for author in authors:
            if line_authors2changes.get(author):
                number_of_changes = line_authors2changes.get(author)
                line_authors2changes.update({author: number_of_changes+pos})
            else:
                line_authors2changes.update({author: pos})
            pos += 1

        return line_authors2changes

    #calculate the developer knowledge of the line according to the last change on the line
    #Ex.: A and B are 2 users: A -> A -> A -> B
    def calculate_developer_knowledge_line_last_change(self, line):
        #collect the number of changes per author for the line
        line_authors2changes = {}
        changes = line.get('line_changes')
        author = changes[0].get('author').get('name')
        line_authors2changes.update({author: 1})

        return line_authors2changes

    #calculate the developer knowledge of the line according to the number of distinct changes on the line.
    #Ex.: A and B are 2 users: A -> A -> A -> B is tranformed in A -> B, A -> A -> A -> B -> is trasformed in A -> B -> A
    def calculate_developer_knowledge_line_distinct_changes(self, line):
        #collect the number of changes per author for the line
        line_authors2changes = {}
        changes = line.get('line_changes')
        previous_author = ""
        for change in changes:
            author = change.get('author').get('name')
            if author != previous_author:
                if line_authors2changes.get(author):
                    number_of_changes = line_authors2changes.get(author)
                    line_authors2changes.update({author: number_of_changes+1})
                else:
                    line_authors2changes.update({author: 1})
                previous_author = author

        return line_authors2changes


    #calculate the the developer knowledge of the line according to the number of times the lines has been modified.
    #Note that this way of calculating the developer knowledge will benefit the users used to rewrite a lot his own code
    def calculate_developer_knowledge_line_multiple_changes(self, line):
        #collect the number of changes per author for the line
        line_authors2changes = {}
        changes = line.get('line_changes')
        for change in changes:
            author = change.get('author').get('name')
            if line_authors2changes.get(author):
                number_of_changes = line_authors2changes.get(author)
                line_authors2changes.update({author: number_of_changes+1})
            else:
                line_authors2changes.update({author: 1})

        return line_authors2changes

    def calculate_developer_knowledge_line(self, line, type):
        if type == "last_change":
            line_authors2changes = self.calculate_developer_knowledge_line_last_change(line)
        elif type == "multiple_changes":
            line_authors2changes = self.calculate_developer_knowledge_line_multiple_changes(line)
        elif type == "distinct_changes":
            line_authors2changes = self.calculate_developer_knowledge_line_distinct_changes(line)
        elif type == "weighted_distinct_changes":
            line_authors2changes = self.calculate_developer_knowledge_line_weighted_distinct_changes(line)

        return line_authors2changes

    def update_file_authors2changes(self, line_authors2changes, file_authors2changes):
        for lo in line_authors2changes.keys():
            if file_authors2changes.get(lo):
                times = file_authors2changes.get(lo)
                file_authors2changes.update({lo: times+line_authors2changes.get(lo)})
            else:
                file_authors2changes.update({lo: line_authors2changes.get(lo)})

    #calculate the file change authors according to the number of changes the performed on the file
    #Ex.: A and B are 2 users: A -> B -> A -> A -> A
    def calculate_developer_knowledge_file_change_multiple_changes(self, json_entry):
        file_authors2changes = {}
        changes = json_entry.get('file_changes')
        #collect the authors of the changes on the file
        for change in changes:
            author = change.get('author').get('name')
            if file_authors2changes.get(author):
                times = file_authors2changes.get(author)
                file_authors2changes.update({author: times+1})
            else:
                file_authors2changes.update({author: 1})

        return file_authors2changes

    #calculate the file change authors without considering the sequence of multiple changes an author could perform
    #Ex.: A and B are 2 users: A -> B -> A -> A -> A is transformed to A -> B -> A
    def calculate_developer_knowledge_file_change_distinct_changes(self, json_entry):
        file_authors2changes = {}
        changes = json_entry.get('file_changes')
        #collect the authors of the changes on the file
        previous_author = ""
        for change in changes:
            author = change.get('author').get('name')
            if author != previous_author:
                if file_authors2changes.get(author):
                    times = file_authors2changes.get(author)
                    file_authors2changes.update({author: times+1})
                else:
                    file_authors2changes.update({author: 1})
                previous_author = author

        return file_authors2changes

    #calculate the file change authors considering only the last change
    def calculate_developer_knowledge_file_change_last_change(self, json_entry):
        file_authors2changes = {}
        change = json_entry.get('file_changes')[0]
        #collect the authors of the changes on the file
        file_authors2changes.update({change.get('author').get('name'): 1})

        return file_authors2changes

    #calculate the file change authors according to the position of the change in the history of the file
    #Ex.: A, B, D are 3 users: A -> B -> A -> B -> B -> D is converted to A -> B -> A -> B -> D and then
    # A x 1 -> B x 2 -> A x 3 -> B x 4 -> D x 5 so then A = 4, B = 6, D = 5
    def calculate_developer_knowledge_file_change_weighted_distinct_changes(self, json_entry):
        file_authors2changes = {}
        changes = json_entry.get('file_changes')
        changes.reverse()
        #collect the authors of the changes on the file
        previous_author = ""
        authors = []
        for change in changes:
            author = change.get('author').get('name')
            if author != previous_author:
                authors.append(author)
                previous_author = author

        pos = 1
        for author in authors:
            if file_authors2changes.get(author):
                number_of_changes = file_authors2changes.get(author)
                file_authors2changes.update({author: number_of_changes+pos})
            else:
                file_authors2changes.update({author: pos})
            pos += 1

        return file_authors2changes

    def calculate_developer_knowledge_file_change(self, json_entry, type):
        if type == "multiple_changes":
            file_authors2changes = self.calculate_developer_knowledge_file_change_multiple_changes(json_entry)
        elif type == "distinct_changes":
            file_authors2changes = self.calculate_developer_knowledge_file_change_distinct_changes(json_entry)
        elif type == "last_change":
            file_authors2changes = self.calculate_developer_knowledge_file_change_last_change(json_entry)
        elif type == "weighted_distinct_changes":
            file_authors2changes = self.calculate_developer_knowledge_file_change_weighted_distinct_changes(json_entry)

        return file_authors2changes

    def calculate_file_primary_experts(self, json_entry):
        file_authors2changes = {}
        lines = json_entry.get('lines')

        #if the file has lines
        if lines:
            for line in lines:
                line_author2changes = self.calculate_developer_knowledge_line(line, Metrics.OWNERSHIP_CALCULATION)
                self.update_file_authors2changes(line_author2changes, file_authors2changes)
        #if the file is an image, a binary files, etc.
        else:
            file_authors2changes = self.calculate_developer_knowledge_file_change(json_entry, Metrics.OWNERSHIP_CALCULATION)

        #get the file primary experts
        primary_experts = self.get_primary_experts(file_authors2changes)

        return primary_experts

    def calculate_bus_factor_authors(self, json_entry):
        file_authors2changes = {}
        lines = json_entry.get('lines')

        #if the file has lines
        if lines:
            for line in lines:
                line_authors2changes = self.calculate_developer_knowledge_line(line, self.DEVELOPER_KNOWLEDGE_CALCULATION)
                self.update_file_authors2changes(line_authors2changes, file_authors2changes)
        #if the file is an image, a binary files, etc.
        else:
            file_authors2changes = self.calculate_developer_knowledge_file_change(json_entry, self.DEVELOPER_KNOWLEDGE_CALCULATION)

        bus_factor_authors = self.get_bus_factor_authors(file_authors2changes)

        return bus_factor_authors

    def get_top_three_extensions(self, extensions, file_count):
        top3exts = []

        sorted_keys = self.get_sorted_keys(extensions)
        for ext in sorted_keys:
            percentage = round((extensions.get(ext)/float(file_count))*100, 2)
            top3exts.append({'name': ext, 'percentage': percentage})
            if len(top3exts) > 2:
                break

        return top3exts

    def calculate_user_relevance(self, bus_factor_authors, user2relevance):
        for bus_factor_user in bus_factor_authors:
            if user2relevance.get(bus_factor_user[0]):
                relevance = user2relevance.get(bus_factor_user[0])
                user2relevance.update({bus_factor_user[0]: relevance+bus_factor_user[1]})
            else:
                user2relevance.update({bus_factor_user[0]: bus_factor_user[1]})

    def get_user_relevance(self):
        user_relevance = []
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        #Each JSON data per line
        user2relevance = {}
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            bus_factor_authors = self.calculate_bus_factor_authors(json_entry)
            self.calculate_user_relevance(bus_factor_authors, user2relevance)
        repo_json.close()

        bus_factor_project = []
        for bf in self.get_bus_factor_authors(user2relevance):
            bus_factor_project.append(bf[0])
        #calculate percentage for users involved in bus factors
        total_relevance = sum(user2relevance.values())
        sorted_keys = self.get_sorted_keys(user2relevance)
        for ur in sorted_keys:
            percentage = round((user2relevance.get(ur)/float(total_relevance))*100, 2)
            if ur in bus_factor_project:
                user_relevance.append({'name': ur, 'knowledge': percentage, 'type': 'user', 'status': 'in bus factor'})
            else:
                user_relevance.append({'name': ur, 'knowledge': percentage, 'type': 'user', 'status': 'not in bus factor'})

        #add to user_relevance the users that are not important for the project
        not_important_users = list(self.USERS - set(sorted_keys))
        for niu in not_important_users:
            user_relevance.append({'name': niu, 'knowledge': 0, 'type': 'user', 'status': 'not in bus factor'})

        return user_relevance

    def get_repo_dirs(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        dirs = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            if json_entry.get('type') == 'repo':
                for d in json_entry.get('dirs'):
                    dirs.append(d.get('dir'))
        repo_json.close()

        return dirs

    def get_repo_exts(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        exts = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            if json_entry.get('type') == 'repo':
                for d in json_entry.get('exts'):
                    exts.append(d.get('ext'))
        repo_json.close()

        return exts

    def get_repo_branches(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        branches = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            if json_entry.get('type') == 'repo':
                for d in json_entry.get('branches'):
                    branches.append(d.get('branch'))
        repo_json.close()

        return branches

    def collect_repo_extensions(self, ext):
        if self.EXTENSIONS.get(ext):
            current_count = self.EXTENSIONS.get(ext)
            self.EXTENSIONS.update({ext: current_count+1})
        else:
            self.EXTENSIONS.update({ext: 1})

    def collect_repo_users(self, file_changes):
        for fc in file_changes:
            committer = fc.get('committer').get('name')
            author = fc.get('author').get('name')

            self.USERS.add(committer)
            self.USERS.add(author)

    def get_bus_factor_per_file(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        #Each JSON data per line
        bus_factor_per_file = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)

            dirs = json_entry.get('dirs')
            ext = json_entry.get('ext')
            name = json_entry.get('name')
            ref = json_entry.get('ref')

            #collect extensions in repo
            self.collect_repo_extensions(ext)
            #count files in repo
            self.TOTAL_FILES += 1
            #collect users in repo
            self.collect_repo_users(json_entry.get('file_changes'))

            #get bus factor per file and prepare it to be stored in JSON
            bus_factor_entries = []
            for bf in self.calculate_bus_factor_authors(json_entry):
                bus_factor_entries.append({'author': bf[0], 'knowledge': bf[1]})

            bus_factor_per_file.append({'dirs': dirs, 'ext': ext, 'name': name, 'type': 'file', 'ref': ref, 'bus_factor': bus_factor_entries})
        repo_json.close()

        return bus_factor_per_file

    def array2dict_array(self, array):
        dict_array = []
        for a in array:
            dict_array.append({'author': a[0], 'knowledge': a[1]})
        return dict_array

    def get_bus_factor_per_ref(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        #Each JSON data per line
        bus_factor = {}
        bus_factor_per_ref = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            ref = json_entry.get('ref')

            for bf in self.calculate_bus_factor_authors(json_entry):
                author = bf[0]
                knowledge = bf[1]
                if bus_factor.get(ref):
                    users_involvement = bus_factor.get(ref)
                    if users_involvement.get(author):
                        old_knowledge = users_involvement.get(author)
                        users_involvement.update({author: old_knowledge+knowledge})
                    else:
                        users_involvement.update({author: knowledge})
                else:
                    bus_factor.update({ref: {author: knowledge}})
        repo_json.close()

        for bf in bus_factor.keys():
            authors_in_bus_factor = self.get_bus_factor_authors(bus_factor.get(bf))
            bus_factor_per_ref.append({'name': bf, 'type': 'ref', 'bus_factor': self.array2dict_array(authors_in_bus_factor)})

        return bus_factor_per_ref

    def get_bus_factor_per_extension(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        #Each JSON data per line
        bus_factor = {}
        bus_factor_per_extension = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            ext = json_entry.get('ext').split('.')[-1].lower()

            for bf in self.calculate_bus_factor_authors(json_entry):
                author = bf[0]
                knowledge = bf[1]
                if bus_factor.get(ext):
                    users_involvement = bus_factor.get(ext)
                    if users_involvement.get(author):
                        old_knowledge = users_involvement.get(author)
                        users_involvement.update({author: old_knowledge+knowledge})
                    else:
                        users_involvement.update({author: knowledge})
                else:
                    bus_factor.update({ext: {author: knowledge}})
        repo_json.close()

        for bf in bus_factor.keys():
            authors_in_bus_factor = self.get_bus_factor_authors(bus_factor.get(bf))
            bus_factor_per_extension.append({'name': bf, 'type': 'ext', 'bus_factor': self.array2dict_array(authors_in_bus_factor)})

        return bus_factor_per_extension

    def get_bus_factor_per_directory(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        #Each JSON data per line
        bus_factor = {}
        bus_factor_per_directory = []
        for json_line in repo_json:
            json_entry = json.loads(json_line)
            ref = json_entry.get('ref')
            dirs = json_entry.get('dirs')
            if not dirs:
                dirs = ['repository_root']

            for bf in self.calculate_bus_factor_authors(json_entry):
                author = bf[0]
                knowledge = bf[1]

                for dir in dirs:
                    if bus_factor.get(dir):
                        users_involvement = bus_factor.get(dir)[1]
                        if users_involvement.get(author):
                            old_knowledge = users_involvement.get(author)
                            users_involvement.update({author: old_knowledge+knowledge})
                        else:
                            users_involvement.update({author: knowledge})
                    else:
                        bus_factor.update({dir: [ref, {author: knowledge}]})
        repo_json.close()

        for bf in bus_factor.keys():
            ref = bus_factor.get(bf)[0]
            authors_in_bus_factor = self.get_bus_factor_authors(bus_factor.get(bf)[1])
            bus_factor_per_directory.append({'name': bf, 'type': 'dir', 'ref': ref, 'bus_factor': self.array2dict_array(authors_in_bus_factor)})

        return bus_factor_per_directory

    def get_project_info(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        json_entry = json.loads(repo_json.readlines()[1])
        if json_entry.get('repo'):
            name = json_entry.get('repo')

        return {'name': name}

    def get_extensions_relevance(self):
        top3exts = self.get_top_three_extensions(self.EXTENSIONS, self.TOTAL_FILES)

        return top3exts

    def threshold_info(self):
        if self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION == self.DEFAULT:
            primary_expert_knowledge = "1ofD"
        else:
            primary_expert_knowledge = str(self.PRIMARY_EXPERT_KNOWLEDGE_PROPORTION)

        secondary_expert_prop = str(self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION)

        thresholds = ".thresholds" + ".primary-expert-" + primary_expert_knowledge \
                     + ".secondary-expert-proportion-" + secondary_expert_prop

        return thresholds

    def export_bus_factor_information(self):
        start_time = datetime.now()

        bus_factor_per_ref = self.get_bus_factor_per_ref()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "/.references.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'references': bus_factor_per_ref}) + "\n")
        bus_factor_json.close()
        del bus_factor_per_ref

        bus_factor_per_directory = self.get_bus_factor_per_directory()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "/dirs.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'dirs': bus_factor_per_directory}) + "\n")
        bus_factor_json.close()
        del bus_factor_per_directory

        bus_factor_per_file = self.get_bus_factor_per_file()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "/files.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'files': bus_factor_per_file}) + "\n")
        bus_factor_json.close()
        del bus_factor_per_file

        bus_factor_per_extension = self.get_bus_factor_per_extension()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "exts.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'exts': bus_factor_per_extension}) + "\n")
        bus_factor_json.close()
        del bus_factor_per_extension

        user_relevance = self.get_user_relevance()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "user_relevance.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'user_relevance': user_relevance}) + "\n")
        bus_factor_json.close()
        del user_relevance

        extension_relevance = self.get_extensions_relevance()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "extension_relevance.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'extension_relevance': extension_relevance}) + "\n")
        bus_factor_json.close()
        del extension_relevance

        project_info = self.get_project_info()
        bus_factor_json = codecs.open(self.JSON_BUS_FACTOR_DIR + "project_info.json", 'w', 'utf-8')
        bus_factor_json.write(json.dumps({'project_info': project_info}) + "\n")
        bus_factor_json.close()
        del project_info

        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("bus factor metric: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")