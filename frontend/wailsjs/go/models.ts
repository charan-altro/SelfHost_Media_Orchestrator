export namespace main {
	
	export class DirectoryItem {
	    name: string;
	    path: string;
	
	    static createFrom(source: any = {}) {
	        return new DirectoryItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.path = source["path"];
	    }
	}
	export class Drive {
	    label: string;
	    path: string;
	
	    static createFrom(source: any = {}) {
	        return new Drive(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.label = source["label"];
	        this.path = source["path"];
	    }
	}
	export class FileSystemNode {
	    current_path: string;
	    parent_path: string;
	    directories: DirectoryItem[];
	
	    static createFrom(source: any = {}) {
	        return new FileSystemNode(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.current_path = source["current_path"];
	        this.parent_path = source["parent_path"];
	        this.directories = this.convertValues(source["directories"], DirectoryItem);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace models {
	
	export class BackgroundTask {
	    id: string;
	    name: string;
	    status: string;
	    progress: number;
	    total: number;
	    message: string;
	    duration: number;
	    // Go type: time
	    created_at: any;
	    // Go type: time
	    updated_at: any;
	
	    static createFrom(source: any = {}) {
	        return new BackgroundTask(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.status = source["status"];
	        this.progress = source["progress"];
	        this.total = source["total"];
	        this.message = source["message"];
	        this.duration = source["duration"];
	        this.created_at = this.convertValues(source["created_at"], null);
	        this.updated_at = this.convertValues(source["updated_at"], null);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class CastMember {
	    name: string;
	    role: string;
	    thumb: string;
	
	    static createFrom(source: any = {}) {
	        return new CastMember(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.role = source["role"];
	        this.thumb = source["thumb"];
	    }
	}
	export class Episode {
	    id: number;
	    season_id: number;
	    episode_number: number;
	    title: string;
	    plot: string;
	    air_date: string;
	    file_path: string;
	    original_filename: string;
	    thumbnail_path: string;
	    resolution: string;
	    video_codec: string;
	    audio_codec: string;
	    missing: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Episode(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.season_id = source["season_id"];
	        this.episode_number = source["episode_number"];
	        this.title = source["title"];
	        this.plot = source["plot"];
	        this.air_date = source["air_date"];
	        this.file_path = source["file_path"];
	        this.original_filename = source["original_filename"];
	        this.thumbnail_path = source["thumbnail_path"];
	        this.resolution = source["resolution"];
	        this.video_codec = source["video_codec"];
	        this.audio_codec = source["audio_codec"];
	        this.missing = source["missing"];
	    }
	}
	export class Library {
	    id: number;
	    name: string;
	    path: string;
	    type: string;
	    language: string;
	
	    static createFrom(source: any = {}) {
	        return new Library(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.path = source["path"];
	        this.type = source["type"];
	        this.language = source["language"];
	    }
	}
	export class MovieFile {
	    id: number;
	    movie_id: number;
	    file_path: string;
	    original_filename: string;
	    size_bytes: number;
	    resolution: string;
	    hdr_type: string;
	    video_codec: string;
	    audio_codec: string;
	    audio_channels: string;
	    part_number: number;
	    subtitle_path: string;
	
	    static createFrom(source: any = {}) {
	        return new MovieFile(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.movie_id = source["movie_id"];
	        this.file_path = source["file_path"];
	        this.original_filename = source["original_filename"];
	        this.size_bytes = source["size_bytes"];
	        this.resolution = source["resolution"];
	        this.hdr_type = source["hdr_type"];
	        this.video_codec = source["video_codec"];
	        this.audio_codec = source["audio_codec"];
	        this.audio_channels = source["audio_channels"];
	        this.part_number = source["part_number"];
	        this.subtitle_path = source["subtitle_path"];
	    }
	}
	export class Movie {
	    id: number;
	    library_id: number;
	    library: Library;
	    title: string;
	    sort_title: string;
	    original_title: string;
	    year: number;
	    tmdb_id: string;
	    imdb_id: string;
	    plot: string;
	    tagline: string;
	    genres: string[];
	    cast: string[];
	    cast_details: CastMember[];
	    director: string;
	    content_rating: string;
	    runtime: number;
	    tmdb_rating: number;
	    imdb_rating: number;
	    tmdb_votes: number;
	    imdb_votes: number;
	    metascore: number;
	    poster_path: string;
	    fanart_path: string;
	    status: string;
	    nfo_generated: boolean;
	    file_renamed: boolean;
	    trailer_url: string;
	    files: MovieFile[];
	
	    static createFrom(source: any = {}) {
	        return new Movie(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.library_id = source["library_id"];
	        this.library = this.convertValues(source["library"], Library);
	        this.title = source["title"];
	        this.sort_title = source["sort_title"];
	        this.original_title = source["original_title"];
	        this.year = source["year"];
	        this.tmdb_id = source["tmdb_id"];
	        this.imdb_id = source["imdb_id"];
	        this.plot = source["plot"];
	        this.tagline = source["tagline"];
	        this.genres = source["genres"];
	        this.cast = source["cast"];
	        this.cast_details = this.convertValues(source["cast_details"], CastMember);
	        this.director = source["director"];
	        this.content_rating = source["content_rating"];
	        this.runtime = source["runtime"];
	        this.tmdb_rating = source["tmdb_rating"];
	        this.imdb_rating = source["imdb_rating"];
	        this.tmdb_votes = source["tmdb_votes"];
	        this.imdb_votes = source["imdb_votes"];
	        this.metascore = source["metascore"];
	        this.poster_path = source["poster_path"];
	        this.fanart_path = source["fanart_path"];
	        this.status = source["status"];
	        this.nfo_generated = source["nfo_generated"];
	        this.file_renamed = source["file_renamed"];
	        this.trailer_url = source["trailer_url"];
	        this.files = this.convertValues(source["files"], MovieFile);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	export class Season {
	    id: number;
	    show_id: number;
	    season_number: number;
	    episode_count: number;
	    poster_path: string;
	    episodes: Episode[];
	
	    static createFrom(source: any = {}) {
	        return new Season(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.show_id = source["show_id"];
	        this.season_number = source["season_number"];
	        this.episode_count = source["episode_count"];
	        this.poster_path = source["poster_path"];
	        this.episodes = this.convertValues(source["episodes"], Episode);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class TVShow {
	    id: number;
	    library_id: number;
	    library: Library;
	    title: string;
	    year: number;
	    tmdb_id: string;
	    tvdb_id: string;
	    imdb_id: string;
	    plot: string;
	    genres: string[];
	    cast: string[];
	    cast_details: CastMember[];
	    director: string;
	    runtime: number;
	    content_rating: string;
	    tmdb_rating: number;
	    imdb_rating: number;
	    tmdb_votes: number;
	    metascore: number;
	    poster_path: string;
	    fanart_path: string;
	    status: string;
	    episode_ordering: string;
	    trailer_url: string;
	    seasons: Season[];
	
	    static createFrom(source: any = {}) {
	        return new TVShow(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.library_id = source["library_id"];
	        this.library = this.convertValues(source["library"], Library);
	        this.title = source["title"];
	        this.year = source["year"];
	        this.tmdb_id = source["tmdb_id"];
	        this.tvdb_id = source["tvdb_id"];
	        this.imdb_id = source["imdb_id"];
	        this.plot = source["plot"];
	        this.genres = source["genres"];
	        this.cast = source["cast"];
	        this.cast_details = this.convertValues(source["cast_details"], CastMember);
	        this.director = source["director"];
	        this.runtime = source["runtime"];
	        this.content_rating = source["content_rating"];
	        this.tmdb_rating = source["tmdb_rating"];
	        this.imdb_rating = source["imdb_rating"];
	        this.tmdb_votes = source["tmdb_votes"];
	        this.metascore = source["metascore"];
	        this.poster_path = source["poster_path"];
	        this.fanart_path = source["fanart_path"];
	        this.status = source["status"];
	        this.episode_ordering = source["episode_ordering"];
	        this.trailer_url = source["trailer_url"];
	        this.seasons = this.convertValues(source["seasons"], Season);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace services {
	
	export class ArtworkInfo {
	    filename: string;
	    path: string;
	    size_bytes: number;
	
	    static createFrom(source: any = {}) {
	        return new ArtworkInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.filename = source["filename"];
	        this.path = source["path"];
	        this.size_bytes = source["size_bytes"];
	    }
	}

}

